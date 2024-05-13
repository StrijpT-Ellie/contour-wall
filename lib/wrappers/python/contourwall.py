import numpy as np
import serial.tools.list_ports
import ctypes
from ctypes import c_void_p, c_char_p, c_uint32, c_uint8, c_bool
from sys import platform
import time

class ContourWallCore(ctypes.Structure):
    _fields_ = [
        ("tiles_ptr", c_void_p),
        ("tiles_len", c_uint32),
    ]

class ContourWall:
    def __init__(self) -> None:
        """Constructor for the ContourWall class."""

        # Load the Rust shared object
        if platform == "win32":
            self.__lib = ctypes.CDLL("./contourwall_core.dll")
        elif platform in ["darwin", "linux"]:
            self.__lib = ctypes.CDLL("./contourwall_core.so")
        else:
            raise Exception(f"'{platform}' is not a supported operating system")

        self._new = self.__lib.new
        self._new.argtypes = [c_uint32]
        self._new.restype = ContourWallCore
    
        self._new_with_ports = self.__lib.new_with_ports
        self._new_with_ports.argtypes = [ctypes.POINTER(c_char_p), ctypes.POINTER(c_char_p), ctypes.POINTER(c_char_p), ctypes.POINTER(c_char_p), ctypes.POINTER(c_char_p), ctypes.POINTER(c_char_p), c_uint32]
        self._new_with_ports.restype = ContourWallCore

        self._single_new_with_port = self.__lib.single_new_with_port
        self._single_new_with_port.argtypes = [c_char_p, c_uint32]
        self._single_new_with_port.restype = ContourWallCore

        self._configure_threadpool = self.__lib.configure_threadpool
        self._configure_threadpool.argtypes = [c_uint8]
        self._configure_threadpool.restype = c_bool

        self._show = self.__lib.show
        self._show.argtypes = [ctypes.POINTER(ContourWallCore)]

        self._update_all = self.__lib.update_all
        self._update_all.argtypes = [ctypes.POINTER(ContourWallCore), ctypes.POINTER(c_uint8), c_bool]

        self._solid_color = self.__lib.solid_color
        self._solid_color.argtypes = [ctypes.POINTER(ContourWallCore), c_uint8, c_uint8, c_uint8]

        self._drop = self.__lib.drop
        self._drop.argtypes = [ctypes.POINTER(ContourWallCore)]

        self.pixels: np.ndarray = np.zeros((20, 20, 3), dtype=np.uint8)
        self.pushed_frames: int = 0

    def new(self, baudrate: int=2_000_000) -> None:
        """Create a new instance of ContourWallCore with 0 tiles"""

        self._cw_core = self._new(baudrate)

    def new_with_ports(self, port1: str, port2: str, port3: str, port4: str, port5: str, port6: str, baudrate: int =2_000_000) -> None:
        """Create a new instance of ContourWallCore with 6 tiles"""

        if check_comport_existence([port1, port2, port3, port4, port5, port6]):
            self._cw_core = self._new_with_ports(port1.encode(), port2.encode(), port3.encode(), port4.encode(), port5.encode(), port6.encode(), baudrate)
        else:
            raise Exception(f"one of the COM ports does not exist")

    def single_new_with_port(self, port: str, baudrate: int =2_000_000) -> None:
        """Create a new instance of ContourWallCore with 1 tile"""

        if check_comport_existence([port]):
            self._cw_core = self._single_new_with_port(port.encode(), baudrate)
        else:
            raise Exception(f"COM port '{port}' does not exist")

    def show(self, sleep_ms:int=0, optimize:bool=True) -> None:
        """
        Update each individual LED in the ContourWallCore object with the pixel data in 'cw.pixels'.

        Example code::
                ``` 
                cw.pixels[:] = [255, 0, 0]
                cw.show() 
                ```
        """
        
        ptr: ctypes._Pointer[c_uint8] = ctypes.cast(ctypes.c_char_p(self.pixels.tobytes()), ctypes.POINTER(ctypes.c_uint8))
        self._update_all(ctypes.byref(self._cw_core), ptr, optimize)
        self._show(ctypes.byref(self._cw_core))
        self.pushed_frames += 1
        time.sleep(sleep_ms/1000)

    def fill_solid(self, r: int, g: int, b: int) -> None:
        """
        fill_solid is a function that fills the entire ContourWall with a single color. Each seperate LED will have the same color.
        
        Example code to make the entire ContourWall red: 
        
        cw.fill_solid(255, 0, 0)
        """

        self._solid_color(ctypes.byref(self._cw_core), r, g, b)
        self.pixels[:] = r, g, b

    def drop(self) -> None:
        """Drop the ContourWallCore instance"""

        self._drop(ctypes.byref(self._cw_core))

def hsv_to_rgb(hue: int, saturation: float, value: float) -> tuple[int, int, int]:
    hue_float: float = hue/255
    saturation /= 255
    value /= 255

    if saturation == 0.0:
        return int(value * 255), int(value * 255), int(value * 255)

    i = int(hue_float * 6.)  # saturationegment number (0 to 5)
    f = (hue_float * 6.) - i  # fractional part of hue_float
    p = value * (1. - saturation)
    q = value * (1. - saturation * f)
    t = value * (1. - saturation * (1. - f))

    if i == 0:
        return int(value * 255), int(t * 255), int(p * 255)
    elif i == 1:
        return int(q * 255), int(value * 255), int(p * 255)
    elif i == 2:
        return int(p * 255), int(value * 255), int(t * 255)
    elif i == 3:
        return int(p * 255), int(q * 255), int(value * 255)
    elif i == 4:
        return int(t * 255), int(p * 255), int(value * 255)
    else:
        return int(value * 255), int(p * 255), int(q * 255)

def check_comport_existence(COMports: list[str]) -> bool:
    """Check for existing COM ports"""
    
    for COMport in COMports:
        if not any(port.device == COMport for port in serial.tools.list_ports.comports()):
            return False
    return True