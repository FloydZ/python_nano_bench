#!/usr/bin/env python3 
"""
"""

from typing import List
import re


class Asm:
    """
    simple class parsing intel x86-64 syntax
    """

    __list_registers = ["rax", "rcx", "rdx"]
    __p = re.compile(r"\[.+\]")

    @staticmethod
    def generate_init_asm_string(used_registers: List[str]) -> str:
        """
        :param used_registers 
        """
        ret = ""
        for i, r in enumerate(used_registers):
            # "MOV RAX, R14; SUB RAX, 8; MOV [RAX], RAX"
            d = 8 * (i + 1)
            ret += f"mov {r}, r14; sub {r}, {d}; mov [{r}], {r};"
        return ret

    @staticmethod
    def parse(s: List[str]):
        """
        parses a single code of intel assembly. Only checks for:
            - memory access
        :param s: line of intel code
        """
        free_registers = Asm.__list_registers
        used_registers = []
        for i, line in enumerate(s):
            t = Asm.__p.search(line)
            if t:
                if len(free_registers) == 0:
                    raise Exception("no free registers anymore")
                r = free_registers[0]
                used_registers.append(r)
                free_registers = free_registers[1:]
                new_line = re.sub(Asm.__p, "[" + r + "]", line)
                s[i] = new_line

        return s, Asm.generate_init_asm_string(used_registers)
