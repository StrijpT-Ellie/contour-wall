import numpy as np
import serial.tools.list_ports
import ctypes
from ctypes import c_void_p, c_char_p, c_uint32, c_uint8, c_uint16, c_uint64
from sys import platform

class ContourWallCore(ctypes.Structure):
    _fields_ = [
        ("frame_time", c_uint64),
        ("serial", c_void_p),
        ("last_serial_write_time", c_uint64)
    ]

class ContourWall:
    def __init__(self, COMport: str, baud_rate=2_000_000):
        # Load the Rust shared object
        if platform == "win32":
            self.__lib = ctypes.CDLL("./cw_core.dll")
        elif platform in ["darwin", "linux"]:
            self.__lib = ctypes.CDLL("./cw_core.so")
        else:
            raise Exception(f"'{platform}' is not a supported operating system")

        self._new = self.__lib.new
        self._new.argtypes = [c_char_p, c_uint32]
        self._new.restype = ContourWallCore

        self._command_0_show = self.__lib.command_0_show
        self._command_0_show.argtypes = [ctypes.POINTER(ContourWallCore)]
        self._command_0_show.restype = c_uint8

        self._command_1_solid_color = self.__lib.command_1_solid_color
        self._command_1_solid_color.argtypes = [ctypes.POINTER(ContourWallCore), c_uint8, c_uint8, c_uint8]
        self._command_1_solid_color.restype = c_uint8

        self._command_2_update_all = self.__lib.command_2_update_all
        self._command_2_update_all.argtypes = [ctypes.POINTER(ContourWallCore), ctypes.POINTER(c_uint8)]
        self._command_2_update_all.restype = c_uint8

        self._command_3_update_specific_led = self.__lib.command_3_update_specific_led
        self._command_3_update_specific_led.argtypes = [ctypes.POINTER(ContourWallCore), ctypes.POINTER(c_uint8), c_uint32]
        self._command_3_update_specific_led.restype = c_uint8

        self._command_4_get_tile_identifier = self.__lib.command_4_get_tile_identifier
        self._command_4_get_tile_identifier.argtypes = [ctypes.POINTER(ContourWallCore)]
        self._command_4_get_tile_identifier.restype = c_uint16

        self._get_frame_time = self.__lib.get_frame_time
        self._get_frame_time.argtypes = [ctypes.POINTER(ContourWallCore), c_uint64]
                
        self._set_frame_time = self.__lib.set_frame_time
        self._set_frame_time.argtypes = [ctypes.POINTER(ContourWallCore)]
        self._set_frame_time.restype = c_uint64

        self._drop = self.__lib.drop
        self._drop.argtypes = [ctypes.POINTER(ContourWallCore)]

        if any(port.device == COMport for port in serial.tools.list_ports.comports()):
            self._cw_core = self._new(COMport.encode(), baud_rate)
        else:
            raise Exception(f"COM port \"{COMport}\", does not exist")

        self.pixels: np.array = np.zeros((20, 20, 3), dtype=np.uint8)
        self.__index_converter: np.array = np.zeros((20, 20), dtype=np.uint16)
        self.__generate_index_conversion_matrix()
        self.pushed_frames: int = 0

    def show(self) -> int:
        buffer = np.zeros(1200, dtype=np.uint8)

        for (x, row) in enumerate(self.pixels):
            for (y, pixel) in enumerate(row):
                buffer[self.__index_converter[x, y]*3+0] = pixel[2]
                buffer[self.__index_converter[x, y]*3+1] = pixel[1]
                buffer[self.__index_converter[x, y]*3+2] = pixel[0]

        ptr = ctypes.cast(buffer.tobytes(), ctypes.POINTER(ctypes.c_uint8))

        res = self._command_2_update_all(ctypes.byref(self._cw_core), ptr) 
        if res != 100:
            return res

        self.pushed_frames += 1
        return self._command_0_show(ctypes.byref(self._cw_core))
    
    def solid_color(self, red: int, green: int, blue: int):
        self.pixels[:] = [blue % 256, green % 256, red % 256]
        self._command_1_solid_color(ctypes.byref(self._cw_core), red % 256, green % 256, blue % 256)
        return self._command_0_show(ctypes.byref(self._cw_core))
    
    def get_identifer(self) -> tuple[int, int]:
        res = self._command_4_get_tile_identifier(ctypes.byref(self._cw_core))
        return (res >> 8, res & 255)
    
    def __generate_index_conversion_matrix(self):
        for x in range(20):
            row_start_value = x
            if x >= 15:
                row_start_value = 300 + x - 15
            elif x >= 10:
                row_start_value = 200 + x - 10
            elif x >= 5:
                row_start_value = 100 + x - 5

            y = 0
            for index in range(row_start_value, row_start_value+100, 5):
                self.__index_converter[x, y] = index
                y += 1

def hsv_to_rgb(h: int, s: int, v: int) -> tuple[int, int, int]:
    h /= 255
    s /= 255
    v /= 255

    if s == 0.0:
        return int(v * 255), int(v * 255), int(v * 255)

    i = int(h * 6.)  # segment number (0 to 5)
    f = (h * 6.) - i  # fractional part of h
    p = v * (1. - s)
    q = v * (1. - s * f)
    t = v * (1. - s * (1. - f))

    if i == 0:
        return int(v * 255), int(t * 255), int(p * 255)
    elif i == 1:
        return int(q * 255), int(v * 255), int(p * 255)
    elif i == 2:
        return int(p * 255), int(v * 255), int(t * 255)
    elif i == 3:
        return int(p * 255), int(q * 255), int(v * 255)
    elif i == 4:
        return int(t * 255), int(p * 255), int(v * 255)
    else:
        return int(v * 255), int(p * 255), int(q * 255)
