# Python Contour Wall Wrapper 

If you have not yet compiled the core library, you find a setup script in the README in the root of the repository. Or start here first by compiling it yourself:

-  **[Setup Guide - Compile the core library](../lib/wrappers/README.md)**

## How to run a demo

After compiling the core library, connect your device (Raspberry Pi, Jetson, laptop, etc.) to the Contour Wall. Example demos can be found in the [/demos](../../../demos/) directory.

Running is done like this:
```bash
python3 -m pip install -r requirements.txt
python3 demo.py
```

## Example Usage
Create a new file and use the import 'from contourwall import ContourWall, hsv_to_rgb', to be able to use the python wrapper.

To utilize this library, ensure you have the necessary serial port permissions and ESP32 firmware flashed with the ContourWall protocol support.

``` Python
from contourwall import ContourWall, hsv_to_rgb

cw = ContourWall()
cw.new()

for i in range(0, 360):
    cw.pixels[:] =  hsv_to_rgb(i, 100, 100)
    cw.show()
cw.fill_solid(0, 0, 0)
cw.show()
```
---

## Using the Emulator (no physical wall needed)

When you’re not near the Contour Wall, you can use the Emulator. The emulator behaves exactly like the real wall:

- Same API 
- Same frame format 

The only difference is that it renders the output on your screen instead of on the hardware.

### Starting the emulator

The emulator is located in [/lib/wrapper/contourwall_emulator](./contourwall_emulator.py), or can be found in the release folder for your architecture. Since the API is very similar you only need to change the import of the `ContourWall` class.

``` Python
# from `ContourWall` to `ContourWallEmulator`
from contourwall_emulator import ContourWallEmulator, hsv_to_rgb

# Also changed from `ContourWall` to `ContourWallEmulator`
cw = ContourWallEmulator()
cw.new()

for i in range(0, 360):
    cw.pixels[:] =  hsv_to_rgb(i, 100, 100)
    cw.show()
cw.fill_solid(0, 0, 0)
cw.show()
```
Now every frame you send will appear in a window on your computer using OpenCV.

---
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
To check types in the wrapper:
- `python3 -m mypy contourwall.py --disallow-untyped-defs --allow-redefinition`









