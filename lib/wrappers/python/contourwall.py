import numpy as np
import serial.tools.list_ports
import ctypes
from ctypes import c_void_p, c_char_p, c_uint32, c_uint8, c_bool
from sys import platform
import time

class ContourWallCore(ctypes.Structure):
    """
    ContourWallCore is a ctypes structure that is used to communicate with the Rust shared object. It contains the following fields:
    - tiles_ptr: A pointer to an array of tiles in the Rust shared object, based on the phisical tiles which together are called the 'Contour Wall'.
    - tiles_len: The length of the tiles array in the Rust shared object, also known as the total count of objects in the array.
    """
    _fields_ = [
        ("tiles_ptr", c_void_p),
        ("tiles_len", c_uint32),
    ]

class ContourWall:
    def __init__(self) -> None:
        """
        Constructor for the ContourWall class.

        The constructor loads the Rust shared object (called ContourWallCore) and initializes the functions that are used to communicate with the Rust shared object.
        """

        # Load the Rust library based on the operating system
        if platform == "win32":
            self.__lib = ctypes.CDLL("./contourwall_core.dll")
        elif platform in ["darwin", "linux"]:
            self.__lib = ctypes.CDLL("./contourwall_core.so")
        else:
            raise Exception(f"'{platform}' is not a supported operating system")

        # Initialize all existing Rust functions in the Python Wrapper
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

        # Drop the ContourWallCore instance
        self._drop = self.__lib.drop
        self._drop.argtypes = [ctypes.POINTER(ContourWallCore)]

        # Initialize the pixel array
        self.pixels: np.ndarray = np.zeros((20, 20, 3), dtype=np.uint8)

        # Initialize the pushed frames counter
        self.pushed_frames: int = 0

    def new(self, baudrate: int=2_000_000) -> None:
        """
        Create a new instance of ContourWallCore, using the default baudrate of 2_000_000.

        This function is used to create a new instance of ContourWallCore when the COM ports are unknown. 
        The function will automaticaly search for available comports, if no COM ports are found a error will be returned.

        Example code:
        ```
            cw = ContourWall()
            cw.new()
        ```
        This example code will create a new instance of ContourWallCore with the default baudrate of 2_000_000 and will try to find available COM ports.
        """

        self._cw_core = self._new(baudrate)

    def new_with_ports(self, port1: str, port2: str, port3: str, port4: str, port5: str, port6: str, baudrate: int =2_000_000) -> None:
        """
        Create a new instance of ContourWallCore, using the default baudrate of 2_000_000 and defining the COM ports for 6 tiles.
        
        This function is used to create a new instance of ContourWallCore when the COM ports are known.
        
        Example code:
        ```
            cw = ContourWall()
            cw.new_with_ports("COM3", "COM4", "COM5", "COM6", "COM7", "COM8")
        ```
        This example code will create a new instance of ContourWallCore with the default baudrate of 2_000_000 and will use the COM ports "COM3", "COM4", "COM5", "COM6", "COM7" and "COM8".
        """

        if check_comport_existence([port1, port2, port3, port4, port5, port6]):
            self._cw_core = self._new_with_ports(port1.encode(), port2.encode(), port3.encode(), port4.encode(), port5.encode(), port6.encode(), baudrate)
        else:
            raise Exception(f"one of the COM ports does not exist")

    def single_new_with_port(self, port: str, baudrate: int =2_000_000) -> None:
        """
        Create a new instance of ContourWallCore, using the default baudrate of 2_000_000 and defining the COM port for 1 tile.

        This function is used to create a new instance of ContourWallCore when a single COM port is known.

        Example code:
        ```
            cw = ContourWall()
            cw.single_new_with_port("COM3")
        ```
        This example code will create a new instance of ContourWallCore with the default baudrate of 2_000_000 and will use the COM port "COM3".
        """

        if check_comport_existence([port]):
            self._cw_core = self._single_new_with_port(port.encode(), baudrate)
        else:
            raise Exception(f"COM port '{port}' does not exist")

    def show(self, sleep_ms:int=0, optimize:bool=True) -> None:
        """
        Show the current state of the pixel array on the ContourWall.

        This function is used to show the current state of the pixel array on the ContourWall. 
        The function will push the current state of the pixel array to the ContourWall and will show the pushed frame on the ContourWall.

        Example code:
        ```
            cw.show()
        ```
        This example code will show the current state of the pixel array on the ContourWall.
        """
        
        ptr: ctypes._Pointer[c_uint8] = ctypes.cast(ctypes.c_char_p(self.pixels.tobytes()), ctypes.POINTER(ctypes.c_uint8))
        self._update_all(ctypes.byref(self._cw_core), ptr, optimize)
        self._show(ctypes.byref(self._cw_core))
        self.pushed_frames += 1
        time.sleep(sleep_ms/1000)

    def fill_solid(self, r: int, g: int, b: int) -> None:
        """
        fill_solid is a function that fills the entire ContourWall with one single color.

        This function is used to fill the entire ContourWall with one single color.
        
        Example code to make the entire ContourWall red: 
        ```
            cw.fill_solid(255, 0, 0)
            cw.show()
        ```
        This example code will fill the entire ContourWall with the color red and will show the filled ContourWall.
        """

        self._solid_color(ctypes.byref(self._cw_core), r, g, b)
        self.pixels[:] = r, g, b

    def drop(self) -> None:
        """Drop the ContourWallCore instance"""

        self._drop(ctypes.byref(self._cw_core))

def hsv_to_rgb(hue: int, saturation: float, value: float) -> tuple[int, int, int]:
    """
    Convert HSV to RGB

    This function is used to convert HSV to RGB.

    H, also known as Hue: The hue of the color, ranging from 0 to 380. Hue is a degree on the color wheel from 0 to 380. 0 is red, 120 is green, 240 is blue.
    S, also known as Saturation: The saturation of the color, ranging from 0 to 100. Saturation is a percentage of the maximum saturation.
    V, also known as Value: The value of the color, ranging from 0 to 100. Value is a percentage of the maximum brightness.

    Example code:
    ```
        r, g, b = hsv_to_rgb(0, 100, 100)
    ```
    This example code will convert the color with a hue of 380, a saturation of 100 and a value of 50 to RGB. The result will be a tuple with the RGB values, resulting in [255, 0, 0].
    """

    # Convert hue to a range between 0 and 5
    h_int = int(hue / 60) % 6

    # Handle special case for h=0 and s=0 (pure white)
    if h_int == 0 and saturation == 0:
        return int(value * 255), int(value * 255), int(value * 255)

    # Calculate fractional parts to be used later
    f = hue / 60 - h_int
    p = value * (1 - saturation)
    q = value * (1 - saturation * f)
    t = value * (1 - saturation * (1 - f))

    # Define RGB components based on hue sector
    if h_int == 0:
        r, g, b = value, t, p
    elif h_int == 1:
        r, g, b = q, value, p
    elif h_int == 2:
        r, g, b = p, value, t
    elif h_int == 3:
        r, g, b = p, q, value
    elif h_int == 4:
        r, g, b = t, p, value
    else:
        r, g, b = value, p, q

    # Clamp RGB values to 0-255 range
    r = max(0, min(255, int(r * 255)))
    g = max(0, min(255, int(g * 255)))
    b = max(0, min(255, int(b * 255)))

    return r, g, b

    # # NON WORKING CODE @TODO: review the new code, test which code gives the expected and correct results.
    # hue_float: float = hue/255
    # saturation /= 255
    # value /= 255

    # if saturation == 0.0:
    #     return int(value * 255), int(value * 255), int(value * 255)

    # i = int(hue_float * 6.)  # saturationegment number (0 to 5)
    # f = (hue_float * 6.) - i  # fractional part of hue_float
    # p = value * (1. - saturation)
    # q = value * (1. - saturation * f)
    # t = value * (1. - saturation * (1. - f))

    # if i == 0:
    #     return int(value * 255), int(t * 255), int(p * 255)
    # elif i == 1:
    #     return int(q * 255), int(value * 255), int(p * 255)
    # elif i == 2:
    #     return int(p * 255), int(value * 255), int(t * 255)
    # elif i == 3:
    #     return int(p * 255), int(q * 255), int(value * 255)
    # elif i == 4:
    #     return int(t * 255), int(p * 255), int(value * 255)
    # else:
    #     return int(value * 255), int(p * 255), int(q * 255)

def check_comport_existence(COMports: list[str]) -> bool:
    """
    Check if the COM ports exist.

    This function is used to check if the COM ports exist.

    COMports: A list of COM ports that need to be checked.

    Example code:
    ```
        if check_comport_existence(["COM3", "COM4", "COM5"]):
            print("All COM ports exist")
        else:
            print("One of the COM ports does not exist")
    ```
    """
    
    for COMport in COMports:
        if not any(port.device == COMport for port in serial.tools.list_ports.comports()):
            return False
    return True