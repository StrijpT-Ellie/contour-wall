from __future__ import print_function
import cv2 as cv
import numpy as np
import argparse
import random as rng

rng.seed(12345)

parser = argparse.ArgumentParser(description='Code for Image Segmentation with Distance Transform and Watershed Algorithm.\
    Sample code showing how to segment overlapping objects using Laplacian filtering, \
    in addition to Watershed and Distance Transformation')
parser.add_argument('--input', help='Path to input image.', default='sauce/pose.png')
args = parser.parse_args()

src = cv.imread(cv.samples.findFile(args.input))

cv.imshow('Source Image', src)

src[np.all(src == 255, axis=2)] = 0

# cv.imshow('Black Background Image', src)

kernel = np.array([[1, 1, 1], [1, -8, 1], [1, 1, 1]], dtype=np.float32)

imgLaplacian = cv.filter2D(src, cv.CV_32F, kernel)
sharp = np.float32(src)
imgResult = sharp - imgLaplacian

imgResult = np.clip(imgResult, 0, 255)
imgResult = imgResult.astype('uint8')
imgLaplacian = np.clip(imgLaplacian, 0, 255)
imgLaplacian = np.uint8(imgLaplacian)

# cv.imshow('New Sharped Image', imgResult)

bw = cv.cvtColor(imgResult, cv.COLOR_BGR2GRAY)
_, bw = cv.threshold(bw, 40, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
# cv.imshow('Binary Image', bw)

dist = cv.distanceTransform(bw, cv.DIST_L2, 3)

cv.normalize(dist, dist, 0, 1.0, cv.NORM_MINMAX)
# cv.imshow('Distance Transform Image', dist)

_, dist = cv.threshold(dist, 0.4, 1.0, cv.THRESH_BINARY)

kernel1 = np.ones((3,3), dtype=np.uint8)
dist = cv.dilate(dist, kernel1)
# cv.imshow('Peaks', dist)

dist_8u = dist.astype('uint8')

contours, _ = cv.findContours(dist_8u, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

markers = np.zeros(dist.shape, dtype=np.int32)

for i in range(len(contours)):
    cv.drawContours(markers, contours, i, (i+1), -1)
cv.circle(markers, (5,5), 3, (255,255,255), -1)
markers_8u = (markers * 10).astype('uint8')
# cv.imshow('Markers', markers_8u)

cv.watershed(imgResult, markers)
mark = markers.astype('uint8')
mark = cv.bitwise_not(mark)
colors = []
for contour in contours:
    colors.append((rng.randint(0,256), rng.randint(0,256), rng.randint(0,256)))
dst = np.zeros((markers.shape[0], markers.shape[1], 3), dtype=np.uint8)
for i in range(markers.shape[0]):
    for j in range(markers.shape[1]):
        index = markers[i,j]
        if index > 0 and index <= len(contours):
            dst[i,j,:] = colors[index-1]
# Visualize the final image
# cv.imshow('Final Result', dst)

final = cv.addWeighted(src, 0.5, dst, 0.5, 0)
cv.imshow('combined', final)


cv.waitKey(0)