import numpy as np
import serial

class ContourWall:
    def __init__(self, com_port, baudrate=921_600):
        self.pixels: np.array = np.zeros((20, 20, 3), dtype=int)
        self.__index_converter: np.array = np.zeros((20, 20), dtype=int)
        self.__generate_index_conversion_matrix()
        self.serial = serial.Serial(port=com_port, baudrate=baudrate, timeout=0)

    def show(self):
        # Make sure that self.pixels is in the colorspace BRG
        data = [0] * 1200
        for (x, row) in enumerate(self.pixels):
            for (y, pixel) in enumerate(row):
                data[self.__index_converter[x, y]*3+0] = pixel[0]
                data[self.__index_converter[x, y]*3+1] = pixel[1]
                data[self.__index_converter[x, y]*3+2] = pixel[2]
        
        self.serial.write(bytes(data))

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
