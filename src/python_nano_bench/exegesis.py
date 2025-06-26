#!/usr/bin/env python3
""" wrapper around the `llvm-exegesis` command """


from typing import List, Union


class Exegesis:
    BINARY = 'llvm-exegesis'

    def __init__(self) -> None:
        """
        """
        self.__cmd = []
    
    @staticmethod
    def __run(cmd, outfile: Union[str, None] = None,
              error_file: Union[str, None] = None):
        """
        """
        pass

    @staticmethod
    def __generate_file(cmd):
        """
        generates something like:

        ```
        # LLVM-EXEGESIS-LIVEIN RDI
        # LLVM-EXEGESIS-DEFREG XMM1 42
        vmulps        (%rdi), %xmm1, %xmm2
        vhaddps       %xmm2, %xmm2, %xmm3
        addq $0x10, %rdi
        ```
        """
        pass
    def all_events(self, mode: Union[str, List[str]]) -> []: 
        """
        runs: 
            llvm-exegesis --mode=inverse_throughput --opcode-index=-1
        """
        if mode not in ["uops", "latency", "inverse_throughput"]:
            raise TypeError()
        if isinstance(mode, list):
            ret = []
            for m in mode:
                ret.append(self.all_events(m))
        cmd = ["--mode={mode}", "--opcode-index=-1"]
        tmp = self.__run(cmd, outfile="tmp.out", error_file="error_file")
        return []

    def analysis(self, assembly: List[str]):
        """
        """
        cmd = [Exegesis.BINARY, "--mode=analysis"]

    def filter(self, f: Union[str, List[str]]):
        """
        wrapper around:
            --analysis-filter=<value> - Filter the benchmarks before analysing them
              =all                    -   Keep all benchmarks (default)
              =reg-only               -   Keep only those benchmarks that do *NOT* involve memory
              =mem-only               -   Keep only the benchmarks that *DO* involve memory
        """
        if f not in ["all", "reg-only", "mem-only"]:
            raise TypeError("not correct ")
        self.__cmd += [f"--analysis-filter={f}"]
