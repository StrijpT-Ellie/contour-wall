import numpy as np
from ctypes import Structure, POINTER, CDLL, c_void_p, c_char_p, c_uint32, c_uint8, c_uint16, c_uint64
from sys import platform

class ContourWallCore(Structure):
    _fields_ = [
        ("tiles_ptr", c_void_p),
        ("tiles_len", c_uint32),
    ]

class ContourWall:
    def __init__(self, baud_rate=2_000_000):
        """Constructor for the ContourWall class."""

        # Load the Rust shared object
        if platform == "win32":
            self.__lib = CDLL("../../cw-core/target/debug/contourwall_core.dll")
        elif platform in ["darwin", "linux"]:
            self.__lib = CDLL("./cw_core.so")
        else:
            raise Exception(f"'{platform}' is not a supported operating system")

        self._new = self.__lib.new
        self._new.argtypes = [c_uint32]
        self._new.restype = ContourWallCore

        self._new_with_ports = self.__lib.new_with_ports
        self._new_with_ports.argtypes = [POINTER(c_char_p), POINTER(c_char_p), POINTER(c_char_p), POINTER(c_char_p), POINTER(c_char_p), POINTER(c_char_p), c_uint32]
        self._new_with_ports.restype = ContourWallCore

        self._single_new_with_port = self.__lib.single_new_with_port
        self._single_new_with_port.argtypes = [c_char_p, c_uint32]
        self._single_new_with_port.restype = ContourWallCore

        self.show = self.__lib.show
        self.show.argtypes = [POINTER(ContourWallCore)]
        # self.show.restype = ???

        self.update_all = self.__lib.update_all
        self.update_all.argtypes = [POINTER(ContourWallCore), POINTER(c_uint8)]
        # self.update_all.restype = ???

        self.solid_color = self.__lib.solid_color
        self.solid_color.argtypes = [POINTER(ContourWallCore), c_uint8, c_uint8, c_uint8]
        # self.solid_color.restype = ???

        self.drop = self.__lib.drop
        self.drop.argtypes = [POINTER(ContourWallCore)]
        # self.drop.restype = ???

        self.pixels: np.array = np.zeros((20, 20, 3), dtype=np.uint8)
        self.pushed_frames: int = 0

    def new_with_ports(self, port1: str, port2: str, port3: str, port4: str, port5: str, port6: str):
        """Create a new instance of ContourWallCore with 6 tiles"""

        self._cw_core = self._new_with_ports(port1.encode(), port2.encode(), port3.encode(), port4.encode(), port5.encode(), port6.encode(), 2_000_000)

    def single_new_with_port(self, port: str):
        """Create a new instance of ContourWallCore with 1 tile"""

        self._cw_core = self._single_new_with_port(port, 2_000_000)

    def show(self):
        """Update each single LED on the ContourWallCore with the pixel data in 'cw.pixels'.
        
        Example code: 
        
        cw.pixels[:] = [255, 0, 0]

        cw.show()"""

        self.update_all(self._cw_core, self.pixels.data_as(POINTER(c_uint8)))
        self.show(self._cw_core)

    def fill_solid(self, r: int, g: int, b: int):
        """fill_solid is a function that fills the entire ContourWall with a single color. Each seperate LED will have the same color.
        
        Example code to make the entire ContourWall red: 
        
        cw.fill_solid(255, 0, 0)"""
        self.solid_color(self._cw_core, r, g, b)

    def drop(self):
        """Drop the ContourWallCore instance"""

        self.drop(self._cw_core)
    