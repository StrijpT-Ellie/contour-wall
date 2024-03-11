import ctypes
import serial.tools.list_ports
from ctypes import c_void_p, c_char_p, c_uint32, c_uint8, c_uint64
import sys

class ContourWallCore(ctypes.Structure):
    _fields_ = [
        ("frame_time", c_uint64),
        ("serial", c_void_p),
        ("last_serial_write_time", c_uint64)
    ]

# Parsing the command line arguments (COMport, baudrate, identifier)
args = sys.argv[1:]
if not len(args) == 3:  
    print("[ERROR] Provide three arguments:\n\t > python3 put_tile_addr.py COMPORT BAUDRATE(921600) IDENTIFIER")
    exit()

COMport = args[0]
baudrate = int(args[1])
identifier = int(args[2])

if identifier == 0:
    print("[ERROR] The new identifier is not allowed to be 0")
    exit()

# Opening the library and defining the required functions
lib = ctypes.CDLL("./cw_core.dll")

new = lib.new
new.argtypes = [c_char_p, c_uint32]
new.restype = ContourWallCore

command_5_set_tile_identifier = lib.command_5_set_tile_identifier
command_5_set_tile_identifier.argtypes = [ctypes.POINTER(ContourWallCore), c_uint8]
command_5_set_tile_identifier.restype = c_uint8

# Initializing the ContourWall struct provided by the library
if not any(port.device == COMport for port in serial.tools.list_ports.comports()):
    raise FileNotFoundError(f"COM port \"{COMport}\", does not exist")
    
cw = new(COMport.encode(), baudrate)

# Setting the new identifier
response = command_5_set_tile_identifier(ctypes.byref(cw), identifier)

if response != 100:
    print(f"[ERROR] Tile repsonse code was: {response}")
else:
    print(f"[SUCCES] Tile has new identifier value of {identifier}")