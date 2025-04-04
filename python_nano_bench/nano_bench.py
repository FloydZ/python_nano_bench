#!/usr/bin/env python3
""" wrapper around the `./nanoBench` command """
import re
import subprocess
import sys
import os
import pprint
from typing import Union, List, Tuple
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path

from shutil import copyfile

from cpuid.cpuid import CPUID, micro_arch

PFC_START_ASM = '.quad 0xE0B513B1C2813F04'
PFC_STOP_ASM = '.quad 0xF0B513B1C2813F04'


class NanoBench:
    """
    wrapper around ./nanoBench
    """


    __micro_arch =  ['SNB', 'IVB', 'HSW', 'BDW', 'SKL', 'SKX', 'CLX', 'KBL', 
                     'CFL', 'CNL', 'ADL-P', 'ADL-E']
    march_translation = {
        'ADL-E' : 'AlderLakeE',
        'ADL-P' : 'AlderLakeP',
        'BDW' : 'Broadwell',
        'CLX' : 'CascadeLakeX',
        'HSM' : 'Broadwell',
        'ISV' : 'IvyBridhe',
        'SND' : 'SandyBridge',
        'SKL' : 'Skylake',
        'SKX' : 'SkylakeX',
    }

    def __init__(self):
        # if set to true, all benchmarks will be performed using the kernel 
        # mode. 
        self.kernel_mode = False

        # nanoBennch kernel and user params
        self._verbose = False
        self._remove_empty_events = False
        self._no_mem = False
        self._range = False
        self._min = False
        self._max = False
        self._median = False
        self._avg = False
        self._alignment_offset = 0
        self._initial_warm_up_count = 0
        self._warm_up_count = 0
        self._n_measurements = 0
        self._loop_count = 0
        self._unroll_count = 0
        self._cpu = -1
        self._end_to_end = False
        self._os = False
        self._usr = False
        self._no_normalization = False
        self._df = False
        self._fixed_counters = False
        self._basic_mode = False
        
        # files
        self._code_one_time_init = False
        self._code_late_init = False
        self._code_init = False
        self._asm_one_time_init = False
        self._asm_late_init = False
        self._asm_init = False
        
        # this refers to the `config file` which is used to determine which 
        # performance metrics is supported by the cpu
        self._config = None
        self.config(NanoBench._get_current_cpu_generation())
    
    @staticmethod
    def _get_current_cpu_generation() -> str:
        """
        :return the cpu architecture of the cpu the script is currently run on.
        """
        return micro_arch(CPUID())

    def _get_cpu_configuration_path(self, march: str):
        """
        NOTE: the returned path is relative to ${PATH_OF_THIS_FILE}/deps/nanoBench
        :return the path to the configuration file containing all performance 
            metrics supported by the local cpu.
        """
        march = NanoBench.march_translation[march]
        return f"./configs/cfg_{march}_all.txt"
        #return f"deps/nanoBench/configs/cfg_{march}_all_core.txt"

    @staticmethod
    def _parse_user_nanobench_output(s: List[str],
                                     remove_zeros: bool=False):
        ret = {}
        for line in s:
            splits = line.split(":")
            assert len(splits) == 2
            d = float(splits[1])
            if remove_zeros:
                if d > 0.0:
                    ret[splits[0]] = d
            else: 
                ret[splits[0]] = d

        return ret

    @staticmethod
    def available():
        """ checks if the following programs are available:
            - as
            - objcopy
            - modprobe
        """
        p = Popen(["as", '--version'], stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode != 0:
            print("`as` is not available")
            return False

        p = Popen(["objcopy", '--version'], stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode != 0:
            print("`objcopy` is not available")
            return False

        p = Popen(["modprobe", '--version'], stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode != 0:
            print("`modprobe` is not available")
            return False

        return True

    @staticmethod
    def write_file(filename: Union[str, Path],
                   content: Union[str, bytes],
                   root: bool=False) -> bool:
        """ simple wrapper to write to a file
        :param filename: full path to the file to write to
        :param content: the content to write to the file
        :param root: if true, temporary root rights are needed to write to the 
            given file. Hence a special code path is used.
        """
        if root:
            pass  # TODO
            return False
        else:
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(str(content))
                return True

    @staticmethod
    def read_file(filename: Union[str, Path],
                  root: bool=False) -> str:
        """ simple wrapper to read form a file
        :param filename: the full path to read from
        :param root: if true, temporary root rights are needed to write to the 
            given file. Hence a special code path is used.
        :return the content of the file as a string
        """
        if root:
            pass  # TODO
            return ""
        else:
            with open(filename) as f:
                return f.read()

    @staticmethod
    def run_command(cmds: List[str],
                    root: bool,
                    cwd: str="") -> Tuple[bool, List[str]]:
        """
        :param cmds: list of strings which is a single command
        :param root: if true the command will be executed as root 
        :param cwd: current working dir 
        """
        if root:
            # TODO different super user command
            # use elevate oder so
            cmds = ["sudo"] + cmds

        if cwd == "":
            cwd = os.path.dirname(os.path.realpath(__file__)) 

        pprint.pprint(cmds)
        p = Popen(cmds, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd)
        p.wait()
        assert p.stdout
        if p.returncode != 0:
            print("command failed")
            print(str(p.stdout.read()))
            return False, []

        s = p.stdout.readlines()
        s = [str(a.decode().removesuffix("\n")) for a in s]

        # filter a few things
        s = [a for a in s if not "Note:" in a]
        return True, s

    @staticmethod
    def assemble(code: str, 
                 obj_file: str,
                 asm_file: str = '/tmp/ramdisk/asm.s'):
        """
        needs `as`

        write `code` into `asm_file` and the  assembles the given `asm_file`
        to `obj_file`.

        :return True: if everything is ok
                False: on error
        """
        try:
            if '|' in code:
                code = code.replace('|15', '.byte 0x66,0x66,0x66,0x66,0x66,0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|14', '.byte 0x66,0x66,0x66,0x66,0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|13', '.byte 0x66,0x66,0x66,0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|12', '.byte 0x66,0x66,0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|11', '.byte 0x66,0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|10', '.byte 0x66,0x2e,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|9', '.byte 0x66,0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|8', '.byte 0x0f,0x1f,0x84,0x00,0x00,0x00,0x00,0x00;')
                code = code.replace('|7', '.byte 0x0f,0x1f,0x80,0x00,0x00,0x00,0x00;')
                code = code.replace('|6', '.byte 0x66,0x0f,0x1f,0x44,0x00,0x00;')
                code = code.replace('|5', '.byte 0x0f,0x1f,0x44,0x00,0x00;')
                code = code.replace('|4', '.byte 0x0f,0x1f,0x40,0x00;')
                code = code.replace('|3', '.byte 0x0f,0x1f,0x00;')
                code = code.replace('|2', '.byte 0x66,0x90;')
                code = code.replace('|1', 'nop;')
                code = re.sub(r'(\d*)\*\|(.*?)\|', lambda m: int(m.group(1)) * (m.group(2) + ';'), code)
            code = '.intel_syntax noprefix;' + code + ';1:;.att_syntax prefix\n'
            with open(asm_file, 'w') as f:
                f.write(code);
            subprocess.check_call(['as', asm_file, '-o', obj_file])
            return True
        except subprocess.CalledProcessError as e:
            sys.stderr.write("Error (assemble): " + str(e))
            sys.stderr.write(code)
            return False

    @staticmethod
    def objcopy(source_file: str,
                target_file: str):
        """
        copy the code/text section from `source_file` to `target_file`

        :param source_file:
        :param target_file:
        :return: True/False depending on the return value `objcopy`

        """
        try:
            subprocess.check_call(['objcopy', "-j", ".text", '-O', 'binary', source_file, target_file])
            return True
        except subprocess.CalledProcessError as e:
            sys.stderr.write("Error (objcopy): " + str(e))
            return False

    @staticmethod
    def createBinaryFile(target_file: str, asm: Union[str, None] = None,
                         obj_file: Union[str, None] = None,
                         bin_file: Union[str, None] = None) -> bool:
        """
        :param target_file:
        :param asm:
        :param obj_file:
        :param bin_file
        :return: True/False on success/failure
        """
        if asm:
            obj_file = '/tmp/ramdisk/tmp.o'
            NanoBench.assemble(asm, obj_file)
        if obj_file is not None:
            NanoBench.objcopy(obj_file, target_file)
            return True
        if bin_file is not None:
            copyfile(bin_file, target_file)
            return True

        return False

    @staticmethod
    def getR14Size() -> int:
        """
        NOTE: only available if the kernel module is loaded.
        :return the size in bytes.
        """
        if not hasattr(NanoBench.getR14Size, 'r14Size'):
            with open('/sys/nb/r14_size') as f:
                line = f.readline()
                mb = int(line.split()[2])
                NanoBench.getR14Size.r14Size = mb * 1024 * 1024
        return NanoBench.getR14Size.r14Size

    @staticmethod
    def getAddress(reg):
        """ Returns the address that is stored in R14, RDI, RSI, RBP, or RSP 
        as a hex string.
        NOTE: only available if the kernel module is loaded
        :param reg: register name
        """
        with open('/sys/nb/addresses') as f:
            for line in f:
                lReg, addr = line.strip().split(': ')
                if reg.upper() == lReg:
                    return addr
        raise ValueError('Register/Address not found')

    @staticmethod
    def is_HT_enabled() -> bool:
        """ checks whether hyper threading is enabled
        : returns true/False if HT is enabled or not
        """
        t = NanoBench.read_file("/sys/devices/system/cpu/smt/active", False)
        try:
            t = int(t)
            t = t != 0
            return t
        except Exception as e:
            print("cannot read the SMT state", e)
            return False

    @staticmethod
    def set_HT(state: int) -> bool:
        """ NOTE: Needs root rights
        :param state: either 0 for disable HT
                          or 1 to enable HT
        :return true/false: if it worked or not
        """
        if -1 > state > 1:
            print('either pass 0/1 to disable/enable ht')
            return False

        cmd = ["echo"]
        if state == 0:
            cmd.append("off")
        if state == 1:
            cmd.append("on")

        cmd.append(">")
        cmd.append("/sys/devices/system/cpu/smt/control")
        b, _ = NanoBench.run_command(cmd, True)
        return b

    def prefix(self) -> bool:
        """
        TODO describe
        """
        # TODO check if atom/core
        self.prev_rdpmc = NanoBench.read_file(filename="/sys/bus/event_source/devices/cpu", root=True)
        NanoBench.write_file(filename="/sys/bus/event_source/devices/cpu", content="2", root=True)

        NanoBench.run_command(["modprobe", "--first-time" 'msr'], True)

        # (Temporarily) disable watchdogs, see https://github.com/obilaniu/libpfc
        NanoBench.run_command(["modprobe", "--first-time", "-r", "iTCO_wdt"], True)
        NanoBench.run_command(["modprobe", "--first-time", "-r", "iTCO_vendor_support"], True)

        self.prev_nmi_watchdog = NanoBench.read_file(filename="/proc/sys/kernel/nmi_watchdog", root=True)
        NanoBench.write_file(filename="/proc/sys/kernel/nmi_watchdog", content="0", root=True)
        return True

    def postfix(self):
        """
        TODO describe
        """
        if self.prev_nmi_watchdog != 0:
            NanoBench.write_file(filename="/proc/sys/kernel/nmi_watchdog", content=self.prev_nmi_watchdog, root=True)

        NanoBench.write_file(filename="/sys/bus/event_source/devices/cpu", content=self.prev_rdpmc, root=True)
        return True

    def run(self, asm: str) -> bool:
        """
        TODO describe
        """
        cwd = "./deps/nanoBench/"
        cmd = ["bash"]
        cmd.append("nanoBench.sh")
        cmd.append("-asm")
        #cmd.append("\"" + asm + "\"")
        cmd.append(asm)

        # add config file
        assert self._config
        cmd.append("-config")
        cmd.append(self._config)

        if self._verbose: cmd += ["-verbose"]
        # note supported by user
        # if self._remove_empty_events: cmd += "-remove_empty_events"
        if self._no_mem: cmd += "-no_mem"
        if self._range: cmd += "-range"
        if self._max: cmd += "-max"
        if self._min: cmd += "-min"
        if self._median: cmd += "-median"
        if self._avg: cmd += "-avg"
        if self._alignment_offset: cmd += "-alignment_offset="+str(self._alignment_offset)
        if self._initial_warm_up_count: cmd += "-initial_warm_up_count="+str(self._initial_warm_up_count)
        if self._warm_up_count: cmd += "-warm_up_count="+str(self._warm_up_count)
        if self._n_measurements: cmd += "-n_measurements="+str(self._n_measurements)
        if self._loop_count: cmd += "-loop_count="+str(self._loop_count)
        if self._unroll_count: cmd += "-unroll_count="+str(self._unroll_count)
        if self._cpu != -1: cmd += "-cpu="+str(self._cpu)
        if self._end_to_end: cmd += "-end_to_end"
        if self._os: cmd += "-os"
        if self._usr: cmd += "-usr"
        if self._no_normalization: cmd += "-no_normalization"
        if self._df: cmd += "-df"
        if self._fixed_counters: cmd += "-fixed_counters"
        if self._basic_mode: cmd += "-basic_mode"
        b, s = NanoBench.run_command(cmd, root=True, cwd=cwd)
        if not b:
            return False 
        data = NanoBench._parse_user_nanobench_output(s, self._remove_empty_events)
        pprint.pprint(data)
        return True

    def config(self, march: str):
        """
        :param march: must be in 
        """
        self._config = self._get_cpu_configuration_path(march)

    def verbose(self) -> 'NanoBench':
        """Outputs the results of all performance counter readings."""
        self._verbose = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """Removes events from the output that did not occur."""
        self._remove_empty_events = True
        return self

    def no_mem(self) -> 'NanoBench':
        """The code for reading the perf. ctrs. does not make memory accesses."""
        self._no_mem = True
        return self

    def range(self) -> 'NanoBench':
        """Outputs the range of the measured values (i.e., the minimum and 
        the maximum).
        """
        self._range = True
        return self

    def max(self) -> 'NanoBench':
        """Selects the maximum as the aggregate function."""
        self._max = True
        return self

    def min(self) -> 'NanoBench':
        """Selects the minimum as the aggregate function."""
        self._min = True
        return self

    def median(self) -> 'NanoBench':
        """Selects the median as the aggregate function."""
        self._median = True
        return self

    def avg(self) -> 'NanoBench':
        """Selects the arithmetic mean (excluding the top and bottom 20%% of 
        the values) as the aggregate function.
        """
        self._avg = True
        return self

    def alignment_offset(self, offset: int) -> 'NanoBench':
        """Alignment offset"""
        self._alignment_offset = offset
        return self

    def initial_warm_up_count(self, count: int) -> 'NanoBench':
        """Number of runs before any measurement is performed."""
        self._initial_warm_up_count = count
        return self

    def warm_up_count(self, count: int) -> 'NanoBench':
        """Number of runs before the first measurement gets recorded."""
        self._warm_up_count = count
        return self

    def n_measurements(self, count: int) -> 'NanoBench':
        """Number of times the measurements are repeated."""
        self._n_measurements = count
        return self

    def loop_count(self, count: int) -> 'NanoBench':
        """Number of iterations of the inner loop."""
        self._loop_count = count
        return self

    def unroll_count(self, count: int) -> 'NanoBench':
        """Number of copies of the benchmark code inside the inner loop."""
        self._unroll_count = count
        return self

    def cpu(self, cpu_cnt: int) -> 'NanoBench':
        """ Pins the measurement thread to CPU n."""
        self._cpu = cpu_cnt
        return self

    def end_to_end(self) -> 'NanoBench':
        """Do not try to remove overhead."""
        self._end_to_end = True
        return self
    
    def usr(self) -> 'NanoBench':
        """If 1, counts events at a privilege level greater than 0. 
        NOTE: only for user
        """
        self._user = True
        return self 

    def os(self) -> 'NanoBench':
        """If 1, counts events at a privilege 0. 
        NOTE: only for user
        """
        self._os = True
        return self 

    def no_normalization(self) -> 'NanoBench':
        """The measurement results are not divided by the number of repetitions
        NOTE: only for user
        """
        self._no_normalization = True
        return self 

    def df(self) -> 'NanoBench':
        """Drains front-end buffers between executing code_late_init and code.
        NOTE: only for user
        """
        self._df = True
        return self 

    def fixed_counters(self) -> 'NanoBench':
        """Reads the fixed-function performance counters.
        NOTE: only for user
        """
        self._fixed_counters = True
        return self 

    def basic_mode(self) -> 'NanoBench':
        """enables basic mode
        NOTE: only for user
        """
        self._basic_mode = True
        return self 

def main():
    n = NanoBench()
    n.remove_empty_events().run("ADD RAX, RBX; ADD RBX, RAX")



if __name__ == "__main__":
   main()
