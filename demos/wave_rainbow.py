import cv2
import numpy as np
import time

from contourwall import ContourWall

# Settings
width, height = 20, 20
wave_speed = 10  # Speed of hue shift
wave_shift = 0


def hue_to_rgb(hue):
    """ Convert hue value to RGB color """
    hue = hue % 360  # Ensure hue is within 0-360
    chroma = 1
    h_prime = hue / 60
    x = chroma * (1 - abs(h_prime % 2 - 1))
    if 0 <= h_prime < 1:
        r, g, b = chroma, x, 0
    elif 1 <= h_prime < 2:
        r, g, b = x, chroma, 0
    elif 2 <= h_prime < 3:
        r, g, b = 0, chroma, x
    elif 3 <= h_prime < 4:
        r, g, b = 0, x, chroma
    elif 4 <= h_prime < 5:
        r, g, b = x, 0, chroma
    else:
        r, g, b = chroma, 0, x
    return int(r * 255), int(g * 255), int(b * 255)


def create_rainbow_wave(frame, wave_shift):
    height, width = frame.shape[:2]
    for x in range(width):
        for y in range(height):
            # Create a wave of hues across the image
            hue = (x * 360 / width + wave_shift) % 360
            frame[y, x] = hue_to_rgb(hue)

    wave_shift = (wave_shift + wave_speed) % 360
    return frame


# Create a window
# cv2.namedWindow('Rainbow Wave')

# cw = ContourWall("COM6")

def wave_rainbow():
    global wave_shift

    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame = create_rainbow_wave(frame, wave_shift)

    # Display the frame
    # cv2.imshow('Rainbow Wave', frame)

    # cw.pixels = frame
    # cw.show()

    # Update wave shift
    wave_shift = (wave_shift + wave_speed) % 360
    time.sleep(0.01)
    return frame

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break
    #


