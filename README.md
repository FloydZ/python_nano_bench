# python_nano_bench

A Python wrapper around [nanoBench](https://github.com/andreas-abel/nanoBench) for measuring CPU performance metrics.

## Installation

### Automatic
```bash
pip install https://github.com/FloydZ/python_nano_bench
```

### Manual
```bash
git clone --recursive https://github.com/FloydZ/python_nano_bench
cd python_nano_bench
./build.sh
```

The `./build.sh` command generates the needed executables.
In the case of `nixos` you can simply run `nix-shell`

## Usage

### Python API

Basic usage:

```python
from python_nano_bench.nano_bench import NanoBench

# Create a NanoBench instance
bench = NanoBench()

# Configure the benchmark
bench.verbose().min().n_measurements(10)

# Add register constraints
bench.constraint("rax = 4")
bench.constraint("rbx < rax")

# Run the benchmark with assembly code
bench.run("ADD RAX, RBX; ADD RBX, RAX")
```

### Using as a Library

python_nano_bench can be integrated into your project as a library for more complex benchmarking:

```python
from python_nano_bench.nano_bench import NanoBench
from python_nano_bench.constraints import parse_constrains

# Custom benchmarking function
def benchmark_instruction_sequence(instructions, constraints=None, iterations=100):
    bench = NanoBench()
    
    # Configure benchmarking parameters
    bench.verbose().min().n_measurements(iterations)
    bench.no_mem().loop_count(1000).unroll_count(10)
    
    # Apply constraints if provided
    if constraints:
        for constraint in constraints:
            bench.constraint(constraint)
    
    # Run in kernel mode for more accurate measurements
    bench.prefix()
    try:
        results = bench.run(instructions, kernel=True)
        return results
    finally:
        bench.postfix()

# Example usage
def compare_add_instructions():
    # Test different addition variants
    instructions = [
        "ADD RAX, RBX",
        "ADD RAX, 42",
        "LEA RAX, [RAX+RBX]",
        "INC RAX"
    ]
    
    # Common constraints for all tests
    constraints = [
        "rax = 100",
        "rbx = 50"
    ]
    
    results = {}
    for instr in instructions:
        print(f"Benchmarking: {instr}")
        result = benchmark_instruction_sequence(instr, constraints)
        results[instr] = result
    
    return results

# For custom register initialization
def initialize_with_custom_assembly():
    bench = NanoBench()
    
    # Use direct assembly for initialization
    bench._asm_init = """
    mov rax, 0x1234567890ABCDEF
    vmovdqu ymm0, [rax]
    """
    
    # Run benchmark
    bench.run("VPADDB YMM1, YMM0, YMM0")
```

### Command-Line Interface

The package also provides a CLI for running benchmarks directly from the command line:

```bash
python -m python_nano_bench.cli --asm "ADD RAX, RBX; ADD RBX, RAX" --verbose --min --constraint "rax = 4" --constraint "rbx < rax"
```

#### CLI Options

```
usage: cli.py [-h] -a ASM [-c CONFIG] [--ignore-self-parsed-init] [-k]
              [--user-mode] [-v] [--remove-empty-events] [--no-mem] [--range]
              [--max] [--min] [--median] [--avg] [--alignment-offset ALIGNMENT_OFFSET]
              [--initial-warm-up-count INITIAL_WARM_UP_COUNT]
              [--warm-up-count WARM_UP_COUNT] [--n-measurements N_MEASUREMENTS]
              [--loop-count LOOP_COUNT] [--unroll-count UNROLL_COUNT]
              [--cpu CPU] [--end-to-end] [--os] [--usr] [--no-normalization]
              [--df] [--fixed-counters] [--basic-mode]
              [--constraint CONSTRAINT] [--asm-init ASM_INIT]
              [--set-ht {0,1}]
```

Key options:
- `-a, --asm`: Assembly code to benchmark (required)
- `-c, --config`: CPU architecture to use for configuration
- `-k, --kernel-mode`: Run benchmark in kernel mode
- `-v, --verbose`: Output results of all performance counter readings
- `--constraint`: Register constraints (can be specified multiple times)
- `--set-ht`: Control HyperThreading (0 to disable, 1 to enable)

For a complete list of options, run `python -m python_nano_bench.cli --help`

## Register Constraints

python_nano_bench supports the following register constraint formats:

```
"rax = 4"             # Assign a constant
"rax < 12"            # Less than
"rax <= 13"           # Less than or equal
"0 <= rax < 7"        # Range constraint
"0 < rax < 7"         # Range constraint with strict bounds
"7 > rax >= 0"        # Reverse range constraint
"rax = *4"            # Dereference
"rax = [17]"          # Array allocation
"rax = [0;17]"        # Array with initialization
"rax = [0u8;17]"      # Array with typed initialization
"rax = [0u32;17]"     # Array with typed initialization
"ymm0 = [0u64,1,2,3]" # Vector register initialization
"rbx < rax"           # Register-to-register comparison
```

These constraints help configure the initial state of registers before running benchmarks.

## Advanced Usage

### Integration with Performance Analysis Tools

You can integrate python_nano_bench with other performance analysis tools:

```python
import json
from python_nano_bench.nano_bench import NanoBench
from python_nano_bench.cpuid.cpuid import CPUID, micro_arch

def performance_analysis_pipeline(instruction_set, output_file="results.json"):
    # Get CPU information
    cpu_info = CPUID()
    arch = micro_arch(cpu_info)
    
    bench = NanoBench()
    bench.config(arch)  # Configure for current architecture
    
    results = {}
    for instruction in instruction_set:
        # Configure for specific measurements
        bench.verbose().remove_empty_events()
        bench.n_measurements(50).median()
        
        # Run benchmark
        result = bench.run(instruction)
        results[instruction] = result
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

# Example usage for instruction latency testing
def measure_latency_comparison():
    instructions = [
        # Arithmetic operations
        "ADD RAX, RBX",
        "SUB RAX, RBX",
        "IMUL RAX, RBX",
        "DIV RBX",
        
        # Bitwise operations
        "AND RAX, RBX",
        "OR RAX, RBX",
        "XOR RAX, RBX",
        
        # SIMD operations
        "PADDQ XMM0, XMM1",
        "VADDPD YMM0, YMM1, YMM2"
    ]
    
    return performance_analysis_pipeline(instructions, "instruction_latency.json")
```

### System-Level Controls

```python
from python_nano_bench.nano_bench import NanoBench

# Manage HyperThreading during benchmarks
def benchmark_with_ht_control(assembly_code):
    # Disable HyperThreading for more consistent results
    NanoBench.set_ht(0)
    
    bench = NanoBench()
    # Pin to specific CPU
    bench.cpu(0)
    
    try:
        # Run benchmark
        results = bench.run(assembly_code)
        return results
    finally:
        # Re-enable HyperThreading
        NanoBench.set_ht(1)
```

These examples show how python_nano_bench can be used as a library for more complex performance analysis tasks.
