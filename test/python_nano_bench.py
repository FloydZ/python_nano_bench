#!/usr/bin/env python3
"""
tests chcking the main pythn interface
"""

from python_nano_bench.nano_bench import NanoBench


def test_simple():
    """
    if this test fails, something really strange is off 
    """
    t = "vpaddb ymm0, ymm1, ymm0; vpaddb ymm1, ymm0, ymmword ptr" \
        "[rip + .LCPI0_0]; vpblendvb ymm0, ymm1, ymm0, ymm1;"
    n = NanoBench()
    d = n.remove_empty_events().run(t)
    assert d

    t2 = "ADD RAX, RBX; ADD RBX, RAX"
    d = n.remove_empty_events().run(t2)
    assert d

def test_loop():
    """
    """
    t = """loop:
    add rax, [rsi];
    adc rax, [rsi+rbx];
    shld rcx, rcx, 1;
    shld rcx, rdx, 2;
    dec r15;
    jnz loop;"""
    n = NanoBench()
    d = n.remove_empty_events().run(t)
    assert d

    t2 = "ADD RAX, RBX; ADD RBX, RAX"
    d = n.remove_empty_events().run(t2)
    assert d



def test_flags():
    """ tests all possible flags """
    ts = [
        "ADD RAX, RBX; ADD RBX, RAX",
        "vpaddb ymm0, ymm1, ymm0; vpaddb ymm1, ymm0, ymmword ptr [rax];"\
        "vpblendvb ymm0, ymm1, ymm0, ymm1;"
    ]

    n = NanoBench()
    for t in ts:
        d = n.remove_empty_events().no_mem().run(t)
        assert d
        d = n.remove_empty_events().range().run(t)
        assert d
        d = n.remove_empty_events().max().run(t)
        assert d
        d = n.remove_empty_events().min().run(t)
        assert d
        d = n.remove_empty_events().median().run(t)
        assert d
        d = n.remove_empty_events().avg().run(t)
        assert d
        d = n.remove_empty_events().end_to_end().run(t)
        assert d
        d = n.remove_empty_events().usr().run(t)
        assert d
        d = n.remove_empty_events().os().run(t)
        assert d
        d = n.remove_empty_events().no_normalization().run(t)
        assert d
        d = n.remove_empty_events().df().run(t)
        assert d
        d = n.remove_empty_events().fixed_counters().run(t)
        assert d
        d = n.remove_empty_events().basic_mode().run(t)
        assert d

        d = n.remove_empty_events().alignment_offset(32).run(t)
        assert d
        d = n.remove_empty_events().initial_warm_up_count(32).run(t)
        assert d
        d = n.remove_empty_events().warm_up_count(32).run(t)
        assert d
        d = n.remove_empty_events().n_measurements(32).run(t)
        assert d
        d = n.remove_empty_events().loop_count(32).run(t)
        assert d
        d = n.remove_empty_events().unroll_count(32).run(t)
        assert d
        d = n.remove_empty_events().cpu(1).run(t)
        assert d


if __name__ == "__main__":
    test_simple()
    test_flags()
