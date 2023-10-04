from imutils import paths
import numpy as np
import argparse as argp
import imutils as imu
import cv2 as cv

ap = argp.ArgumentParser()
ap.add_argument("-i", "--images", type=str, required=True, help="path to input directory of images to stitch")
ap.add_argument("-o", "--output", type=str, required=True, help="path to output the images")
args = vars(ap.parse_args())

print("[INFO] loading images...")
imagePaths = sorted(list(paths.list_images(args["images"])))
images = []

for imagePath in imagePaths:
    image = cv.imread(imagePath)
    images.append(image)
    print(imagePath)

print("[INFO] stitching images...")
stitcher = cv.createStitcher() if imu.is_cv3() else cv.Stitcher_create()
(status, stitched) = stitcher.stitch(images)

if status == 0:
    cv.imwrite(args["output"], stitched)
    cv.imshow("Stitched", stitched)
    cv.waitKey(0)

else:
    print("[INFO] image stitching failed ({})".format(status))