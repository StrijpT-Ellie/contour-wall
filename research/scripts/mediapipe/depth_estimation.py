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
import json

parser = argparse.ArgumentParser(description="Script to process images and add pose information.")

parser.add_argument("--dir", type=str, default="default_name", help="Directory from and to which to read and write images.")
parser.add_argument("--model_complexity", type=int, default=1, help="Model complexity.")
parser.add_argument("--static_image", type=bool, default=True, help="Static mode.")

args = parser.parse_args()

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

distances_cm = []
distances_px = []
 
directory = "../../sauce/" + args.dir
images = []

files = os.listdir(directory)

images = [file for file in files if file.lower().endswith(".jpg")]

current_date = datetime.datetime.now().strftime("../results/%Y-%m-%d_%H-%M-%S[" + args.dir + "]")
output_directory = os.path.join("../../results", current_date)
os.makedirs(output_directory, exist_ok=True)

with mpPose.Pose(
       static_image_mode=args.static_image,
       model_complexity=args.model_complexity) as pose:
    for image_name in images:

        img = cv.imread(os.path.join(directory, image_name))
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

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

        width = 1920
        height = 1440
        dimensions = (width, height)

        img = cv.resize(img, dimensions, interpolation= cv.INTER_LINEAR)
        # cv.imshow(image_name, img)

plt.plot(distances_cm, distances_px, marker='o')

plt.title('Pixel Distance vs. Distance in Centimeters')
plt.xlabel('Distance (cm)')
plt.ylabel('Pixel Distance')

plot_output_path = os.path.join(output_directory, "aa_plot_image.png")
plt.savefig(plot_output_path)

data = {
    "pose_data": {
        "model_complexity": args.model_complexity,
        "static_image_mode": args.static_image
    },
    "image_data": {
        "width": width,
        "height": height
    },
    "data": {
        "distances_cm": distances_cm,
        "distances_px": distances_px
    }
}

file_path = os.path.join(output_directory, "ab_config_data_log.json")

with open(file_path, "w") as file:
    json.dump(data, file, indent=4)