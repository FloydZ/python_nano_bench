# What
simple wrapper around [nanoBench]https://github.com/andreas-abel/nanoBench()

# Installation
============

Automatic:
----------
```bash
pip install https://github.com/FloydZ/python_nano_bench
```

Manual:
------
```
git clone --recursive https://github.com/FloydZ/python_nano_bench
cd python_nano_bench
./build.sh
```

The `./build.sh` command generates the needed executables.
In the case of `nixos` you can simply run `nix-shell`

Usage:
======
 
TODO


# Constraints:

There is the possibility to add constraints to your benchmark
```python 
"rax = 4",
"rax < 12",
"rax <= 13",
"0 <= rax < 7",
"0 < rax < 7",
"7 > rax >= 0",
"rax = *4",
"rax = [17]",
"rax = [0;17]",
"rax = [0u8;17]",
"rax = [0u32;17]",
"ymm0 = [0u64, 1,2,3]",
"rbx < rax",
```