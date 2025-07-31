#!/usr/bin/env python3
""" constraint interface"""

import random
from typing import Any, List, Union
from lark import Lark, Transformer, v_args


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
    """ default to 8 bytes (like native int)

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
    """ Convert type to assembly size specifier

    :param typ: in type
    :return: assembly size specifier (BYTE, WORD, DWORD, or QWORD)
    """
    if typ is None:
        typ = ""
    return {
        'u8': 'BYTE',
        'u16': 'WORD',
        'u32': 'DWORD',
        'u64': 'QWORD'
    }.get(typ, 'QWORD')


# pylint: disable=too-many-instance-attributes
class AssemblyEmitter:
    """
    Base class for emitting assembly instruction
    """
    def __init__(self):
        """ Initialize assembly emitter with default configuration

        :return: new AssemblyEmitter instance
        """
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
            "zmm15", "zmm16", "zmm17", "zmm18", "zmm19", "zmm20", "zmm21",
            "zmm22", "zmm23", "zmm24", "zmm25", "zmm26", "zmm27", "zmm28", 
            "zmm29", "zmm30", "zmm31"]

        self.free_regs = self._free_regs + self._free_sse_regs + self._free_avx2_regs + \
                         self._free_avx512_regs


    def __memory_allocation(self,
                            register: str,
                            nr_bytes: int):
        """ Allocate memory and generate instructions to set register to point to it

        :param register: target register to hold memory address
        :param nr_bytes: number of bytes to allocate
        :return: list of assembly instructions
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
        """ Emit instruction to assign value to register

        Emits instructions like: mov {register}, {value}
        NOTE: this class keeps track of which registers are already used

        :param register: name of the register
        :param value: value to set the register to
        :return: None
        :raises ValueError: if register is not free
        """
        if register not in self.free_regs:
            raise ValueError(f"{register} is not free")
        self.free_regs.remove(register)
        t = f"mov {register}, {value};"
        self.instructions.append(t)

    def add_comparison_instruction(self,
                                   comparisons: List[Any]):
        """ Process comparison expressions and emit instructions to satisfy them

        Handles expressions such as:
            - "rax < 12"
            - "rax <= 13"
            - "0 <= rax < 7"
            - "0 < rax < 7"
            - "7 > rax >= 0"

        :param comparisons: list of comparison tuples (left, operator, right)
        :return: result of adding appropriate assignment instruction
        """
        assert 1 <= len(comparisons) <= 2

        def add_comparison_instruction1(c):
            """ Process a single comparison expression

            Handles expressions such as:
                - "rax < 12"
                - "rax <= 13"
            
            :param c: comparison tuple (left, operator, right)
            :return: result of adding appropriate assignment instruction
            """
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
            """ Process a double comparison expression (chained comparisons)

            Handles expressions such as:
                - "0 <= rax < 7"
                - "0 < rax < 7"
                - "7 > rax >= 0"
            
            :param c1: first comparison tuple (left, operator, right)
            :param c2: second comparison tuple (left, operator, right)
            :return: result of adding appropriate assignment instruction
            """
            assert len(c1) == 3
            assert len(c2) == 3
            if ">" in c1[1].value:
                assert ">" in c2[1].value
            if "<" in c1[1].value:
                assert "<" in c2[1].value
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
        """ Process dereference expressions and emit instructions

        Handles expressions such as:
            - "rax = *4"
        
        :param register: register to store the result in
        :param value: value to be dereferenced
        :return: None
        """
        r1, r2 = self.__memory_allocation(register, self.min_memory_offset)
        r3 = f"MOV [{register}], {value};"
        self.instructions.append(r1)
        self.instructions.append(r2)
        self.instructions.append(r3)

    def add_array_instruction(self,
                              register: str,
                              size: Union[int, List[int]],
                              init_value = None):
        """ Process array expressions and emit instructions

        Handles expressions such as:
            - "rax = [17]"
            - "rax = [0;17]"
            - "rax = [0u8;17]"
            - "rax = [0u32;17]"
        
        :param register: register to store the array pointer in
        :param size: size of the array in bytes or as a list
        :param init_value: optional initialization value for array elements
        :return: None
        :raises NotImplementedError: if init_value is provided (initialization not implemented)
        """
        # easy case:  "rax = [17]"
        r1, r2 = self.__memory_allocation(register, size)
        self.instructions.append(r1)
        self.instructions.append(r2)

        # Zero initialization not yet implemented
        if init_value is not None:
            raise NotImplementedError("Array initialization not implemented")

@v_args(inline=True)
class EvalTransformer(Transformer):
    """Transformer for evaluating and transforming constraints."""
    def __init__(self, emitter: AssemblyEmitter):
        """ Initialize the transformer with an assembly emitter

        :param emitter: the assembly emitter to use
        :return: None
        """
        super().__init__()
        self.emitter = emitter

    def assign(self,
               register: str,
               val):
        """ Process assignment expressions

        Parses expressions like:
            rax = 4
        
        :param register: name of the register
        :param val: value to move into the register
        :return: result of calling appropriate instruction method
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
        """ Process comparison expressions

        :param args: variable list of arguments (val1, op1, val2, op2, val3, ...)
        :return: result of calling emitter's add_comparison_instruction
        """
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
        """ Process comparison operator

        :param op: the operator token
        :return: string representation of the operator
        """
        return str(op)

    def deref(self, val):
        """ Process dereference operation

        :param val: the value to dereference
        :return: tuple ('deref', value)
        """
        return 'deref', val

    def array(self, *args):
        """ Process array declaration

        :param args: variable arguments - either single size or (init, length)
        :return: tuple with array information
        :raises ValueError: if invalid array syntax
        """
        if len(args) == 1:
            # e.g., [17]
            return 'array', [args[0]]
        if len(args) == 2:
            init, length = args
            # e.g., [0; 17], [0u8, 17]
            return 'array_repeat', init, length
        raise ValueError("Invalid array syntax")

    def typed_atom(self, val, typ=None):
        """ Process typed values

        :param val: the value
        :param typ: optional type suffix (u8, u16, etc.)
        :return: tuple ('typed_value', value, type)
        """
        return 'typed_value', val, typ if typ else None

    # pylint: disable=invalid-name
    def TYPE_SUFFIX(self, token):
        """ Process type suffix tokens

        :param token: the type suffix token
        :return: string representation of the token
        """
        return str(token)

    def atom(self, val):
        """ Process atomic values

        :param val: the atomic value
        :return: the value unchanged
        """
        return val

    # pylint: disable=invalid-name
    def NAME(self, token):
        """ Process name tokens

        :param token: the name token
        :return: string representation of the token
        """
        return str(token)

    # pylint: disable=invalid-name
    def SIGNED_NUMBER(self, token):
        """ Process signed number tokens

        :param token: the number token
        :return: integer value of the token
        """
        return int(token)


def parse_constrains(text: str):
    """ Parse constraints and generate assembly instructions

    :param text: the constraint text to parse
    :return: list of generated assembly instructions
    """
    a = AssemblyEmitter()
    parser = Lark(GRAMMAR, parser='lalr', transformer=EvalTransformer(a))
    _ = parser.parse(text)
    return a.instructions
