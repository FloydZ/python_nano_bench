#!/usr/bin/env python3
from python_nano_bench.asm import Asm 

def test_simple():
    """
    if this test fails, something really strange is off 
    """
    t = "vpandq  ymm0, ymm0, qword ptr [rip + .LCPI0_1]{1to4}"
    s, i = Asm.parse([t])
    assert s[0] == "vpandq  ymm0, ymm0, qword ptr [rax]{1to4}"
    assert i


if __name__ == "__main__":
    test_simple()
