## How to run

Make sure that you have Rust>=1.75 intstalled, and Python3.10

### Linux

1. Connect the ESP32S3 on the tile to your device (Laptop, PC, Raspberry Pi, etc.)
2. Compile the `cw-core` Rust library using Cargo
    1. `cd cw-rust`
    2. `cargo build --release`
    3. Move the the compiled binary from `./lib/cw-core/target/release/contourwall_core.dll` to `./lib/wrappers/python` and rename it to `cw_core.dll`
3. Install all python dependencies
    1. `python3.10 -m pip install -r requirements.txt` 
4. Your `./lib/wrappers/python` directory should now have these three files: `contourwall.py`, `demo.py`, `cw_core.so`
5. Relace the string `"YOUR COM PORT"` in the `demo.py` script with COM port that the ESP32S3 is connnected to.
 	- Example: `cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)`
6. Run the demo script: `python3.10 demo.py`

### Windows

1. Connect the ESP32S3 on the tile to your device (Laptop, PC, Raspberry Pi, etc.)
2. Compile the `cw-core` Rust library using Cargo
    1. `cd cw-rust`
    2. `cargo build --release`
    3. Move the the compiled binary from `./lib/cw-core/target/release/contourwall_core.so` to `./lib/wrappers/python` and rename it to `cw_core.so`
3. Install all python dependencies
    1. `python3.10 -m pip install -r requirements.txt` 
4. Your `./lib/wrappers/python` directory should now have these three files: `contourwall.py`, `demo.py`, `cw_core.dll`
5. Relace the string `"YOUR COM PORT"` in the `demo.py` script with COM port that the ESP32S3 is connnected to.
    - Example: `cw = ContourWall("COM0", baud_rate=2_000_000)`
6.  Run the demo script: `python3.10 demo.py`