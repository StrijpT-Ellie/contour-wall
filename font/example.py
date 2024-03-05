import cv2 as cv
import numpy as np

from font import put_text, load_character_index

load_character_index()

mat = np.zeros((40, 250, 3))

put_text(mat, "Hello, World!", [1, 0])
put_text(mat, "This is a low-res font for ELLIE (W.I.P.)", [10, 0])
put_text(mat, "It supports most visable ASCII characters", [20, 0])
put_text(mat, "It also places the text on a Numpy array", [30, 0])

cv.namedWindow('text', cv.WINDOW_NORMAL)
cv.resizeWindow('text', 1200, 150)
cv.imshow("text", mat)
cv.waitKey(0) 
cv.destroyAllWindows() 

