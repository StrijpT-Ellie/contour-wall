import cv2 as cv
import numpy as np
import glob

# Define the size of the checkerboard (number of corners)
chessboard_size = (8, 8)  # Change to match your checkerboard

# Prepare object points (coordinates of the checkerboard corners in 3D space)
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

# Lists to store object points and image points from all calibration images
objpoints = []  # 3D points in real-world space
imgpoints = []  # 2D points in image plane

# Define the termination criteria for corner refinement
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Load calibration images from a folder
calibration_images = glob.glob('images/*.png')
print(calibration_images)

# Loop through calibration images and find chessboard corners
for image_file in calibration_images:
    img = cv.imread(image_file)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Attempt to find the corners of the chessboard pattern in the grayscale image
    ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)

    if ret:
        print("ret is true")
        objpoints.append(objp)
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners)

        # Draw the corners on the image (optional)
        cv.drawChessboardCorners(img, chessboard_size, corners2, ret)
        cv.imshow('Chessboard Corners', img)
        cv.waitKey(500)
    else:
        print("poo")

cv.destroyAllWindows()

# Determine image shape based on the first image in imgpoints
print(len(imgpoints))
image_shape = imgpoints[0].shape[::-1]

# Perform camera calibration
retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, image_shape, None, None)

# Perform fisheye correction
new_camera_matrix, roi = cv.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, gray.shape[::-1], 1, gray.shape[::-1])

# Save the calibration results
np.save("camera_matrix.npy", camera_matrix)
np.save("distortion_coefficients.npy", dist_coeffs)

print("Camera calibration completed. Calibration results saved.")
