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
                cv.rectangle(self.matrix, top_left, bottom_right, color,-1)

                border_color = (0, 0, 0) 
                cv.rectangle(self.matrix, top_left, bottom_right, border_color, 1)
                self.pushed_frames += 1

        cv.imshow('Contour Wall Emulator', self.matrix)
        cv.waitKey(1)
        
        if sleep_ms > 0:
            time.sleep(sleep_ms / 1000)
    
    def fill_solid(self, r: int, g: int, b: int):
        self.pixels[:] = r, g, b

