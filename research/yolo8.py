import os
import sys
import time
import math

import cv2 as cv

from ultralytics import YOLO


model = YOLO('yolov8n-pose.pt')  # load a pretrained model (recommended for training)

results = model.predict("sauce/pose.png", imgsz=160, conf=0.5)

for result in results:
    boxes = result.boxes  # Boxes object for bbox outputs
    masks = result.masks  # Masks object for segmentation masks outputs
    probs = result.probs  # Class probabilities for classification outputs

res_plotted = results[0].plot()
# cv.imshow("result", res_plotted)

runs_path = "runs"
cv.imwrite(os.path.join(runs_path, 'test.png'), res_plotted)
cv.waitKey(0)
