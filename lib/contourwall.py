import time
import numpy as np
import serial

class ContourWall:
    def __init__(self, com_port: str, baudrate: int=921_600, frame_time: int=33):
        """
        `ContourWall` is the software abstraction which resembles the real-life Contour Wall

        ### Parameters
        - `com_port`: COM port to which the tile is connected to. (E.G. "ttyS1" for Unix, "COM6" for Windows)
        - `baudrate`: Speed of the UART connection, default is 921.600 (ESP32 upload speed)
        - `frame_time`: The minimum [frametimes](https://en.wikipedia.org/wiki/Frame_rate) in ms. Default value is 33ms, going faster than 33ms is not recommended. 
        
        ### Properties
        - `pixels`: A 3D 20x20 Numpy array, structured the same way as OpenCV for easy compatibility. Color space BGR, not RGB (like OpenCV)
        """
        self.pixels: np.array = np.zeros((20, 20, 3), dtype=np.uint16)
        self.__frame_time = frame_time
        self.__tx_buffer_size: int = len(self.pixels) * len(self.pixels[0]) * 3 # This result in 1200 bytes
        self.__serial = serial.Serial(port=com_port, baudrate=baudrate, timeout=0)
        self.__index_converter: np.array = np.zeros((20, 20), dtype=np.uint16)
        self.__last_serial_write_time: int = 0

        self.__generate_index_conversion_matrix()

    def show(self, force_frame_time: bool=False) -> int:
        """ 
        Writes the pixel colors to the tile. Make sure that self.pixels is in the colorsp
        ace BRG

        ### Parameters
        - `force_delay`: Forces the minimum delay to be taken, regardless if delay has already taken place

        ### Return
        Returns the actual frametime between this and the previous frame in milliseconds
        """
        buffer = [0] * self.__tx_buffer_size 
        # Using a Numpy array with one element to have an 8 bit uint for the CRC. 
        # Python (to my knowledge) does not have such a type
        crc = np.array([0], dtype=np.uint8)

        for (x, row) in enumerate(self.pixels):
            for (y, pixel) in enumerate(row):
                buffer[self.__index_converter[x, y]*3+0] = pixel[0]
                buffer[self.__index_converter[x, y]*3+1] = pixel[1]
                buffer[self.__index_converter[x, y]*3+2] = pixel[2]
                crc[0] += pixel[0] + pixel[1] + pixel[2]
        
        # Adding checksum to serial transmit buffer
        buffer.append(crc[0])
        
        # Sleeping the leftover frametime time, to keep the frametimes consistant
        if force_frame_time:
            time.sleep(self.__frame_time/1000)
        elif time.time_ns() - self.__last_serial_write_time < (self.__frame_time * 1_000_000):
            time_passed = (time.time_ns() - self.__last_serial_write_time)/1_000_000
            time.sleep((self.__frame_time - time_passed)/1_000)

        self.__serial.write(bytes(buffer))

        frame_time = (time.time_ns() - self.__last_serial_write_time) * 1_000_000
        self.__last_serial_write_time = time.time_ns()

        return frame_time

    def set_frame_time(self, frame_time: int):
        """ 
        Sets the frametime of the ContourWall. Having a faster frametime than 33ms is not recommended. 33ms is the default.
        
        ### Parameters
        - `frame_time`: the new frametime in milliseconds
        """
        self.__frame_time = frame_time

    def get_frame_time(self):
        """ Returns the frametime of the ContourWall in milliseconds """
        return self.__frame_time

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
