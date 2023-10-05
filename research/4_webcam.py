import cv2 as cv
import imutils as imu

cam_r = cv.VideoCapture(0, cv.CAP_DSHOW)
cam_l = cv.VideoCapture(1, cv.CAP_DSHOW)

_, image_r = cam_r.read()
_, image_l = cam_l.read()

images = []
images.append(image_r)
images.append(image_l)

stitcher = cv.createStitcher() if imu.is_cv3() else cv.Stitcher_create()
(status, stitched) = stitcher.stitch(images)

cv.imshow('cam_l', image_l)
cv.imshow('cam_r', image_r)

cv.waitKey(0)



if status == 0:
    cv.imshow("l+r", stitched)
    cv.waitKey(0)
    print("[INFO] Stitching done OwO!")
else:
    print("[INFO] image stitching failed ({})".format(status))

