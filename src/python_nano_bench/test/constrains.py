#!/usr/bin/env python3
"""
tests the constraints helper file
"""

from python_nano_bench.constraints import parse_constrains, generate_assembly

def test_simple():
    """
    if this test fails, something really strange is off 
    """
    tests = [
        "rax = 4",
        "rax < 12",
        "rax <= 13",
        "0 <= rax < 7",
        "rax = *4",
        "rax = [17]",
        "rax = [0;17]",
        "rax = [0u8;17]",
        "rax = [0u32;17]",
    ]
    for expr in tests:
        tree = parse_constrains(expr)
        print(f"{expr}  =>  {tree}")

        #asm = generate_assembly(tree)
        #print(f"{asm}")


if __name__ == "__main__":
    test_simple()
