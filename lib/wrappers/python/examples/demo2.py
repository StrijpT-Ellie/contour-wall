import sys
import time
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
WRAPPER_DIR = _THIS_DIR.parent

if str(WRAPPER_DIR) not in sys.path:
    sys.path.insert(0, str(WRAPPER_DIR))

from contourwall import ContourWall

cw = ContourWall()
cw.new_with_ports("/dev/cu.usbmodem564D0089331", "/dev/cu.usbmodem578E0070891", "/dev/cu.usbmodem578E0073621", "/dev/cu.usbmodem578E0073631", "/dev/cu.usbmodem578E0070441", "/dev/cu.usbmodem578E0073651")

cw.pixels[:] = 255, 255, 255
cw.show()