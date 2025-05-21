#!/usr/bin/env bash

# cd into main project directory
cd src/python_nano_bench

# cd into the current deps folder 
cd deps/nanoBench/

# apply patch
git apply < ../nanoBench.patch

make 
cd ../..

# cd back into main directory
cd ../..
