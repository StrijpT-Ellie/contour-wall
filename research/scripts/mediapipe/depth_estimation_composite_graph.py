import cv2 as cv
import mediapipe as mp
import numpy as np
import os
import datetime
import argparse
import re
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import json

parser = argparse.ArgumentParser(
    description="Script to process images and add pose information and generate composite graph."
)

parser.add_argument(
    "--dir",
    type=str,
    default="default_name",
    help="Directory from which to read images.",
)

args = parser.parse_args()

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

all_distances_cm = []
all_distances_px = []

averaged_distances_px = []

plot_colors = [
    "black",
    "blue",
    "red",
    "green",
    "purple",
    "orange",
    "pink",
    "brown",
    "gray",
]

parent_directory = "../../sauce/" + args.dir  # final_location | teacher_table_location

child_dirs = os.listdir(parent_directory)

# List child_dirs in the parent_dir
child_dirs = [
    d
    for d in os.listdir(parent_directory)
    if os.path.isdir(os.path.join(parent_directory, d))
]

with mpPose.Pose(static_image_mode=True, model_complexity=2) as pose:
    # For each child_dir in parent_dirs
    for child_dir in child_dirs:
        child_dir_path = os.path.join(parent_directory, child_dir)
        # Get all image files in child_dir
        image_files = [
            f
            for f in os.listdir(child_dir_path)
            if any(f.lower().endswith(ext) for ext in ".jpg")
        ]

        distances_cm = []
        distances_px = []

        # For all images in child_dir
        for image_name in image_files:
            image_path = os.path.join(child_dir_path, image_name)
            img = cv.imread(image_path)
            imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
            results = pose.process(imgRGB)

            if results.pose_landmarks:
                landmark = results.pose_landmarks.landmark
                mpDraw.draw_landmarks(
                    img, results.pose_landmarks, mpPose.POSE_CONNECTIONS
                )

                shoulder_landmark = mpPose.PoseLandmark.RIGHT_SHOULDER
                nose_landmark = mpPose.PoseLandmark.NOSE

                shoulder_coords = (
                    int((landmark[12].x + landmark[11].x) * img.shape[1] / 2),
                    int((landmark[12].y + landmark[11].y) * img.shape[0] / 2),
                )

                nose_coords = (
                    int(landmark[0].x * img.shape[1]),
                    int(landmark[0].y * img.shape[0]),
                )

                distance_cm = (
                    int(re.findall(r"\d+", image_name)[0])
                    if re.findall(r"\d+", image_name)
                    else 0
                )

                distance_px = np.sqrt(
                    (nose_coords[0] - shoulder_coords[0]) ** 2
                    + (nose_coords[1] - shoulder_coords[1]) ** 2
                )

            distances_cm.append(distance_cm)
            distances_px.append(distance_px)

        all_distances_cm.append(distances_cm)
        all_distances_px.append(distances_px)

# basically how many image files in each person's file
for datapoint_index in range(6):
    average_distance_px = 0
    # basically how many people there are
    for array_index in range(len(all_distances_px)):
        average_distance_px += all_distances_px[array_index][datapoint_index]
        print(all_distances_px[array_index][datapoint_index])

    print(f"end of {datapoint_index} datapoint_index")
    average_distance_px = average_distance_px / len(all_distances_px)
    print("average_distance_px: " + str(average_distance_px))
    averaged_distances_px.append(average_distance_px)

for i in range(len(all_distances_px)):
    color_index = i % len(plot_colors)
    plt.plot(
        all_distances_cm[i],
        all_distances_px[i],
        "-",
        markersize=1,
        color=plot_colors[color_index],
        label=f"Distances for {child_dirs[i]}",
    )

for i in range(len(distances_cm)):
    plt.plot(
        distances_cm[i],
        averaged_distances_px[i],
        ".",
        markersize=5,
        color="black",
    )

print("ALL DISTANCES PX: ")
print(all_distances_px)
print("AVERAGED DISTANCES PX: ")
print(averaged_distances_px)
print("DISTANCES CM: ")
print(distances_cm)
plt.title("Pixel Distance vs. Frames")
plt.xlabel("Distance (cm)")
plt.ylabel("Distance (px)")
plt.legend()
plt.show()
