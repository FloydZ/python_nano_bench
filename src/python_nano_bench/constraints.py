#!/usr/bin/env python3
""" """

from lark import Lark, Transformer, v_args
from typing import Union

# Define the grammar
grammar = r"""
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

@v_args(inline=True)
class EvalTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.instructions = []

    def assign(self, name, val):
        return ('assign', str(name), self.atom(val))

    def comparison(self, *args):
        # args = val1, op1, val2, op2, val3, ...
        comparisons = []
        left = self.atom(args[0])
        for i in range(1, len(args), 2):
            op = args[i]
            right = self.atom(args[i + 1])
            comparisons.append((left, op, right))
            left = right  # For chained comparisons
        return ('comparison', comparisons)

    def comp_op(self, op):
        return str(op)

    def deref(self, val):
        return ('deref', val)

    def array(self, *args):
        if len(args) == 1:
            # e.g., [17]
            return ('array', [args[0]])
        elif len(args) == 2:
            init, length = args
            # e.g., [0; 17], [0u8, 17]
            return ('array_repeat', init, length)  
        else:
            raise ValueError("Invalid array syntax")

    def typed_atom(self, val, typ=None):
        return ('typed_value', val, typ if typ else None)

    def TYPE_SUFFIX(self, t):
        return str(t)

    def atom(self, val):
        return val

    def NAME(self, token):
        return str(token)

    def SIGNED_NUMBER(self, token):
        return int(token)


def parse_constrains(text: str):
    """ TODO """
    parser = Lark(grammar, parser='lalr', transformer=EvalTransformer())
    tree = parser.parse(text) 
    return tree


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


def generate_assign(node):
    """ TODO """
    _, var, value = node

    var_offset = {
        'rax': 8,
        'rbx': 16,
        'rcx': 24,
        # Add more as needed
    }

    if var not in var_offset:
        raise ValueError(f"Unknown variable: {var}")

    offset = var_offset[var]
    asm = ["MOV RAX, R14", f"SUB RAX, {offset}"]

    if isinstance(value, (int, float, str)):
        asm.append(f"MOV [RAX], {int(value)}")

    elif isinstance(value, tuple):
        if value[0] == 'deref':
            inner = value[1]
            if isinstance(inner, (int, float)):
                asm.append(f"MOV RBX, [{int(inner)}]")
            else:
                raise NotImplementedError("Dereferencing variables not yet supported")
            asm.append("MOV [RAX], RBX")

        elif value[0] == 'array':
            # Single-element array literal
            val = value[1][0]
            asm.append("; Allocate array with 1 element")
            asm.append(f"MOV [RAX], {int(val)}")

        elif value[0] == 'array_repeat':
            init, count = value[1], int(value[2])
            typ = None
            val = None
            if isinstance(init, tuple) and init[0] == 'typed_value':
                val, typ = init[1], init[2]
            else:
                val = init

            size = get_type_size(typ)
            asm.append(f"; Allocating array of {count} elements of size {size}")
            asm.append("PUSH RAX")  # Save base addr
            for i in range(count):
                asm.append("POP RAX")
                asm.append(f"MOV RDX, {int(val)}")
                if typ:
                    asm.append(f"MOV {mov_size(typ)} PTR [RAX+{i * size}], DL")
                else:
                    asm.append(f"MOV [RAX+{i * size}], RDX")
                asm.append("PUSH RAX")
            asm.append("POP RAX")  # Restore RAX

        else:
            raise NotImplementedError(f"Unhandled RHS node: {value[0]}")
    else:
        raise NotImplementedError(f"Unsupported value type: {type(value)}")

    return asm


def generate_comparison(node):
    """ TODO """
    _, comparisons = node
    asm = []

    for i, (left, op, right) in enumerate(comparisons):
        left_asm = left
        asm.extend(left_asm)

        right_asm = right
        asm.extend(right_asm)
    return asm

def generate_assembly(tree):
    """
    Generic code generator for AST from EvalTransformer.
    Supports:
        - assignment: ('assign', var_name, value)
        - comparison: ('comparison', [(left, op, right), ...])
    """
    tree = tree.children[0]
    if tree[0] == 'assign':
        return generate_assign(tree)
    elif tree[0] == 'comparison':
        return generate_comparison(tree)
    else:
        print()
        raise NotImplementedError(f"Unsupported AST node: {tree[0]}")
