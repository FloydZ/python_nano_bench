#!/usr/bin/env python3
"""
Command-line interface for NanoBench - a wrapper for nanoBench performance measurements.
"""

import argparse
import sys
from typing import List, Union

from python_nano_bench.nano_bench import NanoBench


def parse_arguments(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: List of command line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="NanoBench CLI - a tool for measuring CPU performance metrics",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Required: assembly code to run
    parser.add_argument(
        "-a", "--asm", 
        required=True,
        help="Assembly code to benchmark"
    )

    # Configuration options
    parser.add_argument(
        "-c", "--config", 
        help="CPU architecture to use for configuration. If not specified, "
             "the current CPU architecture will be used."
    )
    
    parser.add_argument(
        "--ignore-self-parsed-init",
        action="store_true",
        help="Ignore register initialization code detected during parsing"
    )

    # Mode options
    parser.add_argument(
        "-k", "--kernel-mode",
        action="store_true",
        help="Run benchmark in kernel mode"
    )

    parser.add_argument(
        "--user-mode",
        action="store_true",
        help="Run benchmark in user mode"
    )

    # Output options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Output results of all performance counter readings"
    )

    parser.add_argument(
        "--remove-empty-events",
        action="store_true",
        help="Remove events from output that did not occur"
    )

    # Memory options
    parser.add_argument(
        "--no-mem",
        action="store_true",
        help="Code for reading performance counters does not make memory accesses"
    )

    # Measurement options
    parser.add_argument(
        "--range",
        action="store_true",
        help="Output the range of measured values (min and max)"
    )

    parser.add_argument(
        "--max",
        action="store_true",
        help="Select maximum as the aggregate function"
    )

    parser.add_argument(
        "--min",
        action="store_true",
        help="Select minimum as the aggregate function"
    )

    parser.add_argument(
        "--median",
        action="store_true",
        help="Select median as the aggregate function"
    )

    parser.add_argument(
        "--avg",
        action="store_true",
        help="Select arithmetic mean as the aggregate function"
    )

    # Execution parameters
    parser.add_argument(
        "--alignment-offset",
        type=int,
        help="Alignment offset"
    )

    parser.add_argument(
        "--initial-warm-up-count",
        type=int,
        help="Number of runs before any measurement is performed"
    )

    parser.add_argument(
        "--warm-up-count",
        type=int,
        help="Number of runs before the first measurement gets recorded"
    )

    parser.add_argument(
        "--n-measurements",
        type=int,
        help="Number of times the measurements are repeated"
    )

    parser.add_argument(
        "--loop-count",
        type=int,
        help="Number of iterations of the inner loop"
    )

    parser.add_argument(
        "--unroll-count",
        type=int,
        help="Number of copies of the benchmark code inside the inner loop"
    )

    parser.add_argument(
        "--cpu",
        type=int,
        help="Pin the measurement thread to the specified CPU"
    )

    # Additional options
    parser.add_argument(
        "--end-to-end",
        action="store_true",
        help="Do not try to remove overhead"
    )

    parser.add_argument(
        "--os",
        action="store_true",
        help="Count events at privilege level 0 (only for user mode)"
    )

    parser.add_argument(
        "--usr",
        action="store_true",
        help="Count events at privilege level greater than 0 (only for user mode)"
    )

    parser.add_argument(
        "--no-normalization",
        action="store_true",
        help="Do not divide measurement results by the number of repetitions"
    )

    parser.add_argument(
        "--df",
        action="store_true",
        help="Drain front-end buffers between executing code_late_init and code"
    )

    parser.add_argument(
        "--fixed-counters",
        action="store_true",
        help="Read the fixed-function performance counters"
    )

    parser.add_argument(
        "--basic-mode",
        action="store_true",
        help="Enable basic mode"
    )

    # Register constraints
    parser.add_argument(
        "--constraint",
        action="append",
        help="Register constraints (e.g., 'rax = 4', 'rbx < rax'). "
             "Can be specified multiple times."
    )

    # Initialization instructions
    parser.add_argument(
        "--asm-init",
        help="Assembly code for initialization"
    )

    # HyperThreading control
    parser.add_argument(
        "--set-ht",
        type=int,
        choices=[0, 1],
        help="Control HyperThreading: 0 to disable, 1 to enable"
    )

    return parser.parse_args(args)


def configure_nano_bench(args: argparse.Namespace) -> NanoBench:
    """Configure NanoBench instance based on command line arguments.

    Args:
        args: Parsed command line arguments.

    Returns:
        Configured NanoBench instance.
    """
    nano_bench = NanoBench(ignore_self_parsed_init=args.ignore_self_parsed_init)

    # Set CPU architecture configuration if specified
    if args.config:
        nano_bench.config(args.config)

    # Set kernel mode if specified
    if args.kernel_mode:
        nano_bench.kernel_mode = True

    # Apply all options as method calls
    if args.verbose:
        nano_bench.verbose()
    
    if args.remove_empty_events:
        nano_bench.remove_empty_events()
    
    if args.no_mem:
        nano_bench.no_mem()
    
    if args.range:
        nano_bench.range()
    
    if args.max:
        nano_bench.max()
    
    if args.min:
        nano_bench.min()
    
    if args.median:
        nano_bench.median()
    
    if args.avg:
        nano_bench.avg()
    
    if args.alignment_offset is not None:
        nano_bench.alignment_offset(args.alignment_offset)
    
    if args.initial_warm_up_count is not None:
        nano_bench.initial_warm_up_count(args.initial_warm_up_count)
    
    if args.warm_up_count is not None:
        nano_bench.warm_up_count(args.warm_up_count)
    
    if args.n_measurements is not None:
        nano_bench.n_measurements(args.n_measurements)
    
    if args.loop_count is not None:
        nano_bench.loop_count(args.loop_count)
    
    if args.unroll_count is not None:
        nano_bench.unroll_count(args.unroll_count)
    
    if args.cpu is not None:
        nano_bench.cpu(args.cpu)
    
    if args.end_to_end:
        nano_bench.end_to_end()
    
    if args.os:
        nano_bench.os()
    
    if args.usr:
        nano_bench.usr()
    
    if args.no_normalization:
        nano_bench.no_normalization()
    
    if args.df:
        nano_bench.df()
    
    if args.fixed_counters:
        nano_bench.fixed_counters()
    
    if args.basic_mode:
        nano_bench.basic_mode()
    
    # Apply constraints if specified
    if args.constraint:
        for constraint in args.constraint:
            nano_bench.constraint(constraint)
    
    # Set ASM initialization if specified
    if args.asm_init:
        nano_bench._asm_init = args.asm_init

    return nano_bench


def run_benchmark(nano_bench: NanoBench, asm: str, kernel_mode: bool) -> bool:
    """Run the benchmark with the given assembly code.

    Args:
        nano_bench: Configured NanoBench instance.
        asm: Assembly code to benchmark.
        kernel_mode: Whether to run in kernel mode.

    Returns:
        True if the benchmark was successful, False otherwise.
    """
    # Use prefix/postfix for kernel mode
    if kernel_mode:
        nano_bench.prefix()
    
    try:
        result = nano_bench.run(asm, kernel=kernel_mode)
        return result
    finally:
        if kernel_mode:
            nano_bench.postfix()


def handle_ht_control(state: int) -> bool:
    """Handle HyperThreading control.

    Args:
        state: 0 to disable HT, 1 to enable HT.

    Returns:
        True if the operation was successful, False otherwise.
    """
    if NanoBench.is_ht_enabled() and state == 1:
        print("HyperThreading is already enabled")
        return True
    
    if not NanoBench.is_ht_enabled() and state == 0:
        print("HyperThreading is already disabled")
        return True
    
    result = NanoBench.set_ht(state)
    if result:
        print(f"HyperThreading {'enabled' if state == 1 else 'disabled'} successfully")
    else:
        print("Failed to change HyperThreading state")
    
    return result


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    args = parse_arguments(sys.argv[1:])
    
    # Handle HyperThreading control if specified
    if args.set_ht is not None:
        if not handle_ht_control(args.set_ht):
            return 1
        # If we're just setting HT state without running a benchmark, exit
        if not args.asm:
            return 0
    
    # Check if NanoBench dependencies are available
    if not NanoBench.available():
        print("Error: NanoBench dependencies are not available")
        return 1
    
    # Configure NanoBench
    nano_bench = configure_nano_bench(args)
    
    # Run benchmark
    success = run_benchmark(nano_bench, args.asm, args.kernel_mode)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
