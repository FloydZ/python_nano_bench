#!/usr/bin/env python3
""" constraint interface"""

import random
from lark import Lark, Transformer, v_args
from typing import Union, List, Any


# Define the grammar
GRAMMAR = r"""
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS

start: expr

expr: assign
    | comparison

assign: NAME "=" value

comparison: value (COMP_OP value)+

COMP_OP: "<=" | "<" | ">=" | ">" | "==" | "!="

value: deref | array | atom

deref: "*" atom

array: "[" atom "]" | "[" typed_atom ";" atom "]"

typed_atom: atom TYPE_SUFFIX?

TYPE_SUFFIX: "u8" | "u16" | "u32" | "u64"

atom: NAME | SIGNED_NUMBER

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
"""


def get_type_size(typ: Union[str, None]) -> int:
    """
    default to 8 bytes (like native int)
    :param typ: in type
    :return size of the type in bytes
    """
    if typ is None:
        typ = ""
    return {
        'u8':  1,
        'u16': 2,
        'u32': 4,
        'u64': 8,
        'i8':  1,
        'i16': 2,
        'i32': 4,
        'i64': 8
    }.get(typ, 8)


def mov_size(typ: Union[str, None]) -> str:
    if typ is None:
        typ = ""
    return {
        'u8': 'BYTE',
        'u16': 'WORD',
        'u32': 'DWORD',
        'u64': 'QWORD'
    }.get(typ, 'QWORD')

class AssemblyEmitter:
    def __init__(self):
        self.instructions = []
        # min bytes to allocate
        self.min_memory_offset = 8
        # current offset in the memory
        self.memory_offset = 0
        # R14, RDI, RSI, RSP, and RBP are initialized with addresses in the
        # middle of dedicated memory areas (of 1 MB each),
        self.memory_register = "r14" # pointer to a valid memory region

        self._free_regs = ["rax", "rbx", "rcx", "rdx", "r8", "r9", "r10", "r11",
                           "r12", "r13", "r15"]
        self._free_sse_regs = ["xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5",
                               "xmm6", "xmm7", "xmm8", "xmm9", "xmm10", "xmm12", "xmm13", "xmm14",
                               "xmm15"]
        self._free_avx2_regs = ["ymm0", "ymm1", "ymm2", "ymm3", "ymm4", "ymm5",
                                "ymm6", "ymm7", "ymm8", "ymm9", "ymm10", "ymm12", "ymm13", "ymm14",
                                "ymm15"]
        self._free_avx512_regs = ["zmm0", "zmm1", "zmm2", "zmm3", "zmm4", "zmm5",
                                  "zmm6", "zmm7", "zmm8", "zmm9", "zmm10", "zmm12", "zmm13", "zmm14",
                                  "zmm15", "zmm16", "zmm17", "zmm18", "zmm19", "zmm20", "zmm21", "zmm22",
                                  "zmm23", "zmm24", "zmm25", "zmm26", "zmm27", "zmm28", "zmm29", "zmm30",
                                  "zmm31"]

        self.free_regs = self._free_regs + self._free_sse_regs + self._free_avx2_regs + \
                         self._free_avx512_regs


    def __memory_allocation(self,
                            register: str,
                            nr_bytes: int):
        """
            TODO
        """
        # increase the offset for the next allocation
        nr_bytes = max(nr_bytes, self.min_memory_offset)
        self.memory_offset += nr_bytes

        r1 = f"MOV {register}, {self.memory_register};"
        r2 = f"SUB {register}, {self.memory_offset};"
        return [r1, r2]


    def add_assignment_instruction(self,
                                   register: str,
                                   value: Union[str, int]):
        """
        emits instructions like:
            mov {register}, {value}
        NOTE: this class keeps track of which registers are already used
        :param register: name of the register
        :param value: value to set the register to.
        """
        if register not in self.free_regs:
            raise ValueError(f"{register} is not free")
        self.free_regs.remove(register)
        t = f"mov {register}, {value};"
        self.instructions.append(t)

    def add_comparison_instruction(self,
                                   comparisons: List[Any]):
        """
        parses:
            - "rax < 12",
            - "rax <= 13",
            - "0 <= rax < 7",
            - "0 < rax < 7",
            - "7 > rax >= 0",
        """
        assert 1 <= len(comparisons) <= 2

        def add_comparison_instruction1(c):
            assert len(c) == 3
            l, h = 0, c[2].children[0]
            if "=" not in c[1].value:
                h -= 1
            if ">" in c[1].value:
                l, h = h, l
            register = c[0].children[0]
            value = random.randint(l, h)
            return self.add_assignment_instruction(register, value)

        def add_comparison_instruction2(c1, c2):
            assert len(c1) == 3
            assert len(c2) == 3
            if ">" in c1[1].value: assert ">" in c2[1].value
            if "<" in c1[1].value: assert "<" in c2[1].value
            assert c1[2].children[0] == c2[0].children[0]

            register = c1[2].children[0]
            l, h = c1[0].children[0], c2[2].children[0]
            if ">" in c2[1].value:
                l, h = h, l
                c1, c2 = c2, c1
            if "=" not in c1[1].value:
                l += 1
            if "=" not in c2[1].value:
                h -= 1

            assert l < h
            value = random.randint(l, h)
            return self.add_assignment_instruction(register, value)

        if len(comparisons) == 1:
            return add_comparison_instruction1(comparisons[0])
        return add_comparison_instruction2(comparisons[0], comparisons[1])

    def add_dereference_instruction(self,
                                   register: str,
                                   value: Union[str, int]):
        """
        parses:
            -"rax = *4",
        """
        r1, r2 = self.__memory_allocation(register, self.min_memory_offset)
        r3 = f"MOV [{register}], {value};"
        self.instructions.append(r1)
        self.instructions.append(r2)
        self.instructions.append(r3)
        return

    def add_array_instruction(self,
                              register: str,
                              size: Union[int],
                              init_value = None):
        """
        parses
            - "rax = [17]",
            - "rax = [0;17]",
            - "rax = [0u8;17]",
            - "rax = [0u32;17]",
        """
        # easy case:  "rax = [17]"
        r1, r2 = self.__memory_allocation(register, size)
        self.instructions.append(r1)
        self.instructions.append(r2)

        # TODO zero initialization not implemented
        if init_value is not None:
            pass

        return

@v_args(inline=True)
class EvalTransformer(Transformer):
    def __init__(self, emitter: AssemblyEmitter):
        super().__init__()
        self.emitter = emitter

    def assign(self,
               register: str,
               val):
        """ parses: something like:
            ```
                rax = 4
            ```
        :param register: name of the register
        :param val: value to move into the register
        """
        val = val.children[0]
        if isinstance(val, tuple):
            if val[0] == "deref":
                return self.emitter.add_dereference_instruction(register, val[1])
            if val[0] == "array":
                return self.emitter.add_array_instruction(register, val[1][0])
            if val[0] == "array_repeat":
                assert len(val) == 3
                return self.emitter.add_array_instruction(register, val[2], val[1][1])
        return self.emitter.add_assignment_instruction(register, val)

    def comparison(self, *args):
        """ TODO explain"""
        # args = val1, op1, val2, op2, val3, ...
        comparisons = []
        left = self.atom(args[0])
        for i in range(1, len(args), 2):
            op = args[i]
            right = self.atom(args[i + 1])
            comparisons.append((left, op, right))
            # For chained comparisons
            left = right
        assert 1<= len(comparisons) <= 2
        return self.emitter.add_comparison_instruction(comparisons)

    def comp_op(self, op):
        """ TODO """
        return str(op)

    def deref(self, val):
        """ TODO """
        return 'deref', val

    def array(self, *args):
        """ TODO """
        if len(args) == 1:
            # e.g., [17]
            return 'array', [args[0]]
        elif len(args) == 2:
            init, length = args
            # e.g., [0; 17], [0u8, 17]
            return 'array_repeat', init, length
        else:
            raise ValueError("Invalid array syntax")

    def typed_atom(self, val, typ=None):
        """ TODO """
        return 'typed_value', val, typ if typ else None

    def TYPE_SUFFIX(self, token):
        """ TODO """
        return str(token)

    def atom(self, val):
        """ TODO """
        return val

    def NAME(self, token):
        """ TODO """
        return str(token)

    def SIGNED_NUMBER(self, token):
        """ TODO """
        return int(token)


def parse_constrains(text: str):
    """ TODO """
    a = AssemblyEmitter()
    parser = Lark(GRAMMAR, parser='lalr', transformer=EvalTransformer(a))
    _ = parser.parse(text)
    return a.instructions