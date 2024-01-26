import numpy as np
import cv2 as cv

frame = np.zeros((20, 20, 3), dtype=np.uint8)

# Set the bottom right pixel to red (BGR format)
frame[19, 0] = [0, 0, 255]  # BGR: [Blue, Green, Red]

# Display the image
cv.imshow("Frame with Red Pixel", frame)
cv.waitKey(0)
cv.destroyAllWindows()