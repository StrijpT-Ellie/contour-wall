# Manual Setup Guide

This guide explains how to compile the ContourWall core library and use it through the python wrapper. Follow the steps below to get a demo running on the Contour Wall.

- [Python guide](../lib/wrappers/python/README.md)
- [Rust guide](../lib/wrappers/rust/README.md)

## Requirements

Before you start, make sure you have:

- **Rust ≥ 1.75** 
- **Python ≥ 3.10**
- A connected ContourWall

## Linux Setup

1. Compile the `cw-core` Rust library using Cargo
   - `cd ./lib/cw-core &  cargo build --release`
2. Copy these files into your project directory
   - `./lib/cw-core/target/libcontourwall_core.so` as `contourwall_core.so`
   - `./lib/wrapper/python/contourwall.py`
   - `./demos/demo.py`
3. Install all python dependencies: `python3.10 -m pip install -r requirements.txt`
4. Run the demo script: `python3.10 demo.py`
 
## MacOs Setup

1. Compile the `cw-core` Rust library using Cargo
   - `cd ./lib/cw-core &  cargo build --release`
2. Copy these files into your project directory
   - `./lib/cw-core/target/libcontourwall_core.dylib` as `contourwall_core.dylib`
   - `./lib/wrapper/python/contourwall.py`
   - `./demos/demo.py`
3. Install all python dependencies: `python3.10 -m pip install -r requirements.txt`
4. Run the demo script: `python3.10 demo.py`

## Windows

1. Compile the `cw-core` Rust library using Cargo
   - `cd ./lib/cw-core &  cargo build --release`
2. Copy these files into your project directory
   - `./lib/cw-core/target/contourwall_core.dll`
   - `./lib/wrapper/python/contourwall.py`
   - `./demos/demo.py`
3. Install all python dependencies: `python3.10 -m pip install -r requirements.txt`
4. Run the demo script: `python3.10 demo.py`
