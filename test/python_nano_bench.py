#!/usr/bin/env python3
from python_nano_bench.nano_bench import NanoBench 

def test_simple():
    """
    if this test fails, something really strange is off 
    """
    t = "vpaddb ymm0, ymm1, ymm0; vpaddb ymm1, ymm0, ymmword ptr [rip + .LCPI0_0]; vpblendvb ymm0, ymm1, ymm0, ymm1;"
    n = NanoBench()
    d = n.remove_empty_events().run(t)
    assert d


if __name__ == "__main__":
    test_simple()
