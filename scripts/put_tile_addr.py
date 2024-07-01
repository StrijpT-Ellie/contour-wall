import ctypes
import serial.tools.list_ports
from ctypes import c_void_p, c_char_p, c_uint32, c_uint8, c_uint64
import sys

# Parsing the command line arguments (COMport, baudrate, identifier)
args = sys.argv[1:]
if not len(args) == 3:  
    print("[ERROR] Provide three arguments:\n\t > python3 put_tile_addr.py COMPORT BAUDRATE(921600) IDENTIFIER")
    exit()

COMport = args[0]
baudrate = int(args[1])
identifier = int(args[2])
print(args)

if identifier == 0:
    print("[ERROR] The new identifier is not allowed to be 0")
    exit()

# Opening the library and defining the required functions
lib = ctypes.CDLL("./contourwall_core.dll")

set_tile_identifier = lib.set_tile_identifier
set_tile_identifier.argtypes = [c_char_p, c_uint32, c_uint8]
set_tile_identifier.restype = bool

# Initializing the ContourWall struct provided by the library
if not any(port.device == COMport for port in serial.tools.list_ports.comports()):
    raise FileNotFoundError(f"COM port \"{COMport}\", does not exist")

# Setting the new identifier
response = set_tile_identifier(COMport.encode(), baudrate, identifier)

if response:
    print(f"[SUCCES] Tile has new identifier value of {identifier}")
else:
    print(f"[ERROR] Tile repsonse code was: {response}")