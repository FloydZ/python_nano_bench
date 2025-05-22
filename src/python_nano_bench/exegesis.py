#!/usr/bin/env python3
""" wrapper around the `llvm-exegesis` command """


from typing import List

class Exegesis:
    BINARY = 'llvm-exegesis'

    def __init__(self) -> None:
        pass
    
    @staticmethod
    def __run(cmd):
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
    
    def analysis(self, assembly: List[str]):
        """
        """
        cmd = [Exegesis.BINARY, "--mode=analysis"]
