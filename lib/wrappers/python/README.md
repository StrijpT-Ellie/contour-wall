# Python ContourWall Wrapper

## How to run

1. Install Python, version >3.9
2. Install Cargo
3. Install modules: `python3 -m pip install -r requirements.txt`
4. Compile core library located at `contourwall/lib/cw_core`: `cargo build --release`
5. Move compiled library located in `target/release` directory to same directory as `contourwall.py`
6. Run: `python3 demo.py`

## Example Usage
Create a new file and use the import 'from contourwall import ContourWall, hsv_to_rgb', to be able to use the python wrapper.

To utilize this library, ensure you have the necessary serial port permissions and ESP32 firmware flashed with the ContourWall protocol support.

``` Python
from contourwall import ContourWall, hsv_to_rgb

cw = ContourWall()
cw.single_new_with_port("COM3")

for i in range(0, 360):
    cw.pixels[:] =  hsv_to_rgb(i, 100, 100)
    cw.show()
cw.fill_solid(0, 0, 0)
cw.show()
```

## Functions in the python wrapper
|Type|Classes & Functions|Description|
|---|---|---|
|class|`ContourWall`|When this class is called it will be initiated by the `__init__` function.|
|def|`__init__`|This function is used to create an instance of the `ContourWall` class.|
|def|`new`|This function is used to create the `ContourWallCore` object when the COM ports are unknown.|
|def|`new_with_ports`|This function is used to create a new instance of `ContourWallCore` when the COM ports are known.|
|def|`single_new_with_ports`|This function is used to create a new instance of ContourWallCore when a single COM port is known.|
|def|`show`|This function is used to show the current state of the pixel array on the ContourWall.|
|def|`fill_solid`|This function is used to fill the entire ContourWall with one single color.|
|def|`hsv_to_rgb`|This function is used to convert HSV color code to RGB color code.|

## Running MyPy typechecker

- `python3 -m mypy contourwall.py --disallow-untyped-defs`
