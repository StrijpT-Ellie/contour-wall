# Python ContourWall Wrapper

## How to run

1. Install Python, version 3.9 to 3.11
2. Install Cargo
3. Install modules: `python3 -m pip install -r requirements.txt`
4. Compile core library located at `contourwall/lib/cw_core`: `cargo build --release`
5. Move compiled library located in `target/release` directory to same directory as `contourwall.py`
6. Run: `python3 demo.py`

## Running MyPy typechecker

- `python3 -m mypy contourwall.py --disallow-untyped-defs`