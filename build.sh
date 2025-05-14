#!/usr/bin/env bash

# cd into main project directory
cd src/python_nano_bench

cd deps/nanoBench/user
make 
cd ../../..

# cd back into main directory
cd ../..
