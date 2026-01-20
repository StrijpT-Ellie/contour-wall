# Setup Guide - Compile the core library
This guide explains how to compile the **Contour Wall core library** and use it through a wrapper (for example, the Python wrapper). Follow the steps below to get a demo running on the Contour Wall.
After completing this guide you can find more guidance on each wrapper. Each wrapper has its own documentation, examples, and setup instructions:

- [Python guide](../lib/wrappers/python/README.md)
- [Rust guide](../lib/wrappers/rust/README.md)

---

## Requirements

Before you start, make sure you have:

- **Rust ≥ 1.75**
- **Cargo** (comes with Rust)
- **Python 3.10**
- A connected **Contour Wall tile (ESP32-S3)**

---


## Linux Setup

1. Compile the Rust core library using Cargo:

```bash
cd cw-rust
cargo build --release
```
2. Compile the `cw-core` Rust library using Cargo
``` bash
   cd cw-rust
```
``` bash
   cargo build --release
```
   Move the the compiled binary from `./lib/cw-core/target/release/contourwall_core.so` to `./lib/wrappers/python` and rename it to `cw_core.so`

3. Install all python dependencies

``` bash
   python3.10 -m pip install -r requirements.txt
```
4. Your `./lib/wrappers/python` directory should now have these three files: `contourwall.py`, `demo.py`, `cw_core.so`
5. Relace the string `"YOUR COM PORT"` in the `demo.py` script with COM port that the ESP32S3 is connnected to.
 	- Example: `cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)`
6. Run the demo script: `python3.10 demo.py`
 

---

---
## MacOs Setup
1. Compile the Rust core library using Cargo:

```bash
cd cw-rust
cargo build --release
```
2. Compile the `cw-core` Rust library using Cargo
``` bash
   cd cw-rust
```
``` bash
   cargo build --release
```
   Move the the compiled binary from `./lib/cw-core/target/release/contourwall_core.dylib` to `./lib/wrappers/python` and rename it to `cw_core.dylib`

3. Install all python dependencies

``` bash
   python3.10 -m pip install -r requirements.txt
```
4. Your `./lib/wrappers/python` directory should now have these three files: `contourwall.py`, `demo.py`, `cw_core.so`
5. Relace the string `"YOUR COM PORT"` in the `demo.py` script with COM port that the ESP32S3 is connnected to.
 	- Example: `cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)`
6. Run the demo script: `python3.10 demo.py`

----

----

## Windows
1. Compile the `cw-core` Rust library using Cargo

```bash
cd cw-rust
cargo build --release
```
Move the the compiled binary from `./lib/cw-core/target/release/contourwall_core.dll` to `./lib/wrappers/python` and rename it to `cw_core.dll`
2. Install all python dependencies
```bash
   python3.10 -m pip install -r requirements.txt
```
3. Your `./lib/wrappers/python` directory should now have these three files: `contourwall.py`, `demo.py`, `cw_core.dll`
4. Relace the string `"YOUR COM PORT"` in the `demo.py` script with COM port that the ESP32S3 is connnected to.
    - Example: `cw = ContourWall("COM0", baud_rate=2_000_000)`
5. Run the demo script: `python3.10 demo.py`


