import math
import cv2 as cv
import mediapipe as mp
import numpy as np
import os
import datetime
import argparse
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Script to process images and add pose information.")

parser.add_argument("--dir", type=str, default="default_name", help="Directory from and to which to read and write images.")

args = parser.parse_args()

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

distances_cm = []
distances_px = []

# Images should be named like so "honza_250.jpg" i.e. "name_distanceInCm.jpg"
 
directory = "../../sauce/" + args.dir
images = []

files = os.listdir(directory)

images = [file for file in files if file.lower().endswith(".jpg")]

current_date = datetime.datetime.now().strftime("../results/%Y-%m-%d_%H-%M-%S[" + args.dir + "]")
output_directory = os.path.join("../../results", current_date)
os.makedirs(output_directory, exist_ok=True)

with mpPose.Pose(
       static_image_mode=True,
       model_complexity=1) as pose:
    for image_name in images:

        img = cv.imread(os.path.join(directory, image_name))
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

        # Calculate the lenght of the neck for depth estimation (assuming average lenght of a neck is 105mm https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6994911/)
        if results.pose_landmarks:
            landmark = results.pose_landmarks.landmark
            mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

            shoulder_landmark = mpPose.PoseLandmark.RIGHT_SHOULDER
            nose_landmark = mpPose.PoseLandmark.NOSE

            shoulder_coords = (
                int(
                    (landmark[12].x + landmark[11].x) * img.shape[1] / 2
                ),
                int(
                    (landmark[12].y + landmark[11].y) * img.shape[0] / 2
                ),
            )

            nose_coords = (
                int(landmark[0].x * img.shape[1]),
                int(landmark[0].y * img.shape[0]),
            )

            cv.line(img, shoulder_coords, nose_coords, (0, 255, 0), 3)

            distance_px = np.sqrt(
                    (nose_coords[0] - shoulder_coords[0]) ** 2
                    + (nose_coords[1] - shoulder_coords[1]) ** 2
                )
            
            distance_cm = int(re.findall(r'\d+', image_name)[0]) if re.findall(r'\d+', image_name) else 0
            
            cv.putText(img, str(int(distance_px)), (300, 300), cv.FONT_HERSHEY_PLAIN, 20, (0, 255, 0), 20)

        distances_cm.append(distance_cm)
        distances_px.append(distance_px)

        img_output_path = os.path.join(output_directory, image_name)
        cv.imwrite(img_output_path, img)

        wdh = 1920
        hgt = 1440
        dimensions = (wdh, hgt)

        img = cv.resize(img, dimensions, interpolation= cv.INTER_LINEAR)
        # cv.imshow(image_name, img)

plt.plot(distances_cm, distances_px, marker='o')

plt.title('Pixel Distance vs. Distance in Centimeters')
plt.xlabel('Distance (cm)')
plt.ylabel('Pixel Distance')

plot_output_path = os.path.join(output_directory, "plot_image.png")
plt.savefig(plot_output_path)
