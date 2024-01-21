import numpy as np
import serial

class ContourWall:
    def __init__(self, com_port: str, baudrate: int=921_600):
        """
        `ContourWall` is the software abstraction which resembles the real-life Contour Wall

        ### Parameters
        - `com_port`: COM port to which the tile is connected to. (E.G. "ttyS1" for Unix, "COM6" for Windows)
        - `baudrate`: Speed of the UART connection, default is 921.600 (ESP32 upload speed)
        
        ### Properties
        - `pixels`: A 3D 20x20 Numpy array, structured the same way as OpenCV for easy compatibility. Color space BGR, not RGB (like OpenCV)
        """
        self.pixels: np.array = np.zeros((20, 20, 3), dtype=int)
        self.__index_converter: np.array = np.zeros((20, 20), dtype=int)
        self.__generate_index_conversion_matrix()
        self.__serial = serial.Serial(port=com_port, baudrate=baudrate, timeout=0)

    def show(self):
        """ 
        Writes the pixel colors to the tile. Make sure that self.pixels is in the colorspace BRG
        """
        data = [0] * 1200
        crc = np.array([0], dtype='uint8')

        for (x, row) in enumerate(self.pixels):
            for (y, pixel) in enumerate(row):
                data[self.__index_converter[x, y]*3+0] = pixel[0]
                data[self.__index_converter[x, y]*3+1] = pixel[1]
                data[self.__index_converter[x, y]*3+2] = pixel[2]
                crc[0] += pixel[0] + pixel[1] + pixel[2]

        data.append(crc[0])
        
        self.__serial.write(bytes(data))

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
