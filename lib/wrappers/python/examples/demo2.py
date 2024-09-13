from contourwall import ContourWall
import time

cw = ContourWall()
cw.new_with_ports("/dev/cu.usbmodem564D0089331", "/dev/cu.usbmodem578E0070891", "/dev/cu.usbmodem578E0073621", "/dev/cu.usbmodem578E0073631", "/dev/cu.usbmodem578E0070441", "/dev/cu.usbmodem578E0073651")

cw.pixels[:] = 255, 255, 255
cw.show()