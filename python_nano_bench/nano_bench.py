#!/usr/bin/env python3
""" wrapper around the `./nanoBench` command """
import re
import subprocess
import sys
from typing import Union, List, Tuple
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path

from shutil import copyfile

PFC_START_ASM = '.quad 0xE0B513B1C2813F04'
PFC_STOP_ASM = '.quad 0xF0B513B1C2813F04'


class NanoBench:
    """
    wrapper around ./nanoBench
    """
    def __init__(self):
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
        self._alignment_offset = False
        self._initial_warm_up_count = False
        self._warm_up_count = False
        self._n_measurements = False
        self._loop_count = False
        self._unroll_count = False
        self._cpu = False
        self._code_one_time_init = False
        self._code_late_init = False
        self._code_init = False
        self._end_to_end = False

        pass

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
                    root: bool) -> Tuple[bool, str]:
        """
        :param cmfd
        """
        if root:
            # TODO different super user command
            cmds = ["sudo"] + cmds

        p = Popen(cmds, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode != 0:
            print("command failed")
            return False, ""

        assert p.stdout
        s = str(p.stdout.read())
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

        # TODO support a different super user command
        cmd = ["sudo", "echo"]
        if state == 0:
            cmd.append("off")
        if state == 1:
            cmd.append("on")

        cmd.append(">")
        cmd.append("/sys/devices/system/cpu/smt/control")
        p = Popen(cmd, stdin=PIPE, stdout=STDOUT, stderr=STDOUT)
        p.wait()
        if p.returncode != 0:
            print("set HT failed")
            return False

        return True

    def prefix(self) -> bool:
        """

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
        """
        if self.prev_nmi_watchdog != 0:
            NanoBench.write_file(filename="/proc/sys/kernel/nmi_watchdog", content=self.prev_nmi_watchdog, root=True)

        NanoBench.write_file(filename="/sys/bus/event_source/devices/cpu", content=self.prev_rdpmc, root=True)
        return True

    def run(self, asm: str) -> bool:
        """
        """
        if not self.prefix():
            return False

        obj_file = "TODO"
        cmd = ["deps/nanoBench/user/nanoBench", obj_file]
        if self._verbose: cmd += "--verbose"
        if self._remove_empty_events: cmd += "--remove_empty_events"
        NanoBench.run_command(cmd, True)

        if not self.postfix():
            return False

        return True

    def verbose(self) -> 'NanoBench':
        """Outputs the results of all performance counter readings."""
        self._verbose = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def no_mem(self) -> 'NanoBench':
        """"""
        self._no_mem = True
        return self

    def range(self) -> 'NanoBench':
        """"""
        self._ran = True
        return self

    def remove_empgety_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self
    def remove_empty_events(self) -> 'NanoBench':
        """"""
        self._remove_empty_events = True
        return self

