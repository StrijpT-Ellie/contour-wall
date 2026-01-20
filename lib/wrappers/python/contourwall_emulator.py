import numpy as np
import cv2 as cv
import time

class ContourWallEmulator:
    def __init__(self):
        self.__cv_window_name = "ContourWall Emulation"
        
        # Number of rows and collumns on the pixel grid 
        self.rows = 40
        self.cols = 60
        self.cell_size = 10
        self.pushed_frames: int = 0
        
        #Creates a 3D array of shape (rows*cell_size, cols*cell_size, 3) with 8-bit unsigned integers
        self.__matrix = np.zeros((self.rows * self.cell_size, self.cols * self.cell_size, 3), dtype=np.uint8)
        self.pixels: np.ndarray = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)

    def new(self, baudrate: int=2_000_000):
        pass
    
    def new_with_ports(self, port1: str, port2: str, port3: str, port4: str, port5: str, port6: str, baudrate: int =2_000_000):
        pass
    # Method for initializing the emulator with a single port, changing grid size
    def single_new_with_port(self, baudrate: int=2_000_000):
        self.rows = 20
        self.cols = 20
        self.cell_size = 20

        self.matrix = np.zeros((self.rows * self.cell_size, self.cols * self.cell_size, 3), dtype=np.uint8) 
        self.pixels: np.ndarray = np.zeros((self.rows, self.cols, 3), dtype=np.uint8)

    def show(self, sleep_ms:int=0, optimize:bool=True):
        for row in range(self.rows):
            for col in range(self.cols):
                top_left = (col * self.cell_size, row * self.cell_size)
                bottom_right = ((col + 1) * self.cell_size, (row + 1) * self.cell_size)
                color = tuple(int(c) for c in self.pixels[row, col])
                cv.rectangle(self.__matrix, top_left, bottom_right, color,-1)

                border_color = (0, 0, 0) 
                cv.rectangle(self.__matrix, top_left, bottom_right, border_color, 1)
                self.pushed_frames += 1

        cv.imshow('Contour Wall Emulator', self.__matrix)
        cv.waitKey(1)
        
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000)
    
    def fill_solid(self, r: int, g: int, b: int):
        self.pixels[:] = r, g, b

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

    hue: float = float(hue) / 100.0
    saturation /= 100
    value /= 100
    
    if saturation == 0.0: return int(value), int(value), int(value)
        
    i = int(hue*6.0) # XXX assume int() truncates!
    f = (hue*6.0) - i
    i = i%6
    
    p = int(round((value*(1.0 - saturation)) * 255))
    q = int(round((value*(1.0 - saturation*f)) * 255))
    t = int(round((value*(1.0 - saturation*(1.0-f))) * 255))
    value = int(round(value*255))
    
    if i == 0:
        return value, t, p
    if i == 1:
        return q, value, p
    if i == 2:
        return p, value, t
    if i == 3:
        return p, q, value
    if i == 4:
        return t, p, value
    if i == 5:
        return value, p, q
        
    return 0, 0, 0
