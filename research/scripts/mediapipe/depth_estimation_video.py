import os
import cv2 as cv
import mediapipe as mp
import time
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import json
import datetime
import argparse
import statistics

parser = argparse.ArgumentParser(
    description="Script to process images and add pose information."
)

parser.add_argument(
    "--dir",
    type=str,
    default="default_name",
    help="Directory from and to which to read and write images.",
)

args = parser.parse_args()

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
# pose = mpPose.Pose()

WINDOW_SIZE = 10
distances_px = []
distances_px_smooth = [0 for _ in range(0, WINDOW_SIZE - 1)]
frames = []
frame_counter = 0

median_nums = []

directory = "../../sauce/" + args.dir

files = os.listdir(directory)

mp4_files = [file for file in files if file.endswith(".mp4")]
mp4_file = os.path.join(directory, mp4_files[0])

current_date = datetime.datetime.now().strftime(
    "../results/%Y-%m-%d_%H-%M-%S[" + args.dir + "]"
)
output_directory = os.path.join("../../results", current_date)
os.makedirs(output_directory, exist_ok=True)

cap = cv.VideoCapture(mp4_file)

previous_time = 0

with mpPose.Pose(
    model_complexity=1,
) as pose:
    while cap.isOpened():
        _, img = cap.read()

        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)
        landmark = results.pose_landmarks.landmark

        if not _ or landmark[0].y < 0.1:
            break

        if results.pose_landmarks:
            # mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

            shoulder_coords = (
                int((landmark[12].x + landmark[11].x) * img.shape[1] / 2),
                int((landmark[12].y + landmark[11].y) * img.shape[0] / 2),
            )

            hip_coords = (
                int((landmark[24].x + landmark[23].x) * img.shape[1] / 2),
                int((landmark[24].y + landmark[23].y) * img.shape[0] / 2),
            )

            # nose_coords = (
            #     int(landmark[0].x * img.shape[1]),
            #     int(landmark[0].y * img.shape[0]),
            # )

            cv.line(img, shoulder_coords, hip_coords, (0, 255, 0), 3)

            distance_px = np.sqrt(
                (hip_coords[0] - shoulder_coords[0]) ** 2
                + (hip_coords[1] - shoulder_coords[1]) ** 2
            )
            
            frame_counter += 1
            distances_px.append(distance_px)
            frames.append(frame_counter)

            cv.putText(
                img,
                "PXD: " + str(int(distance_px)),
                (50, 100),
                cv.FONT_HERSHEY_PLAIN,
                3,
                (0, 255, 0),
                3,
            )

            median_nums.append(distance_px)

            if len(median_nums) > WINDOW_SIZE - 1:
                distances_px_smooth.append(np.median(median_nums[-WINDOW_SIZE:]))

        current_time = time.time()
        fps = 1 / (current_time - previous_time)
        previous_time = current_time

        cv.putText(
            img,
            "FPS: " + str(int(fps)),
            (50, 50),
            cv.FONT_HERSHEY_PLAIN,
            3,
            (255, 0, 0),
            3,
        )

        cv.imshow("image", img)

        cv.waitKey(1)

print("distances_px lenght: " + str(len(distances_px)))
print("frames lenght: " + str(len(frames)))
print("distances_px_smooth lenght: " + str(len(distances_px_smooth)))

min_length = min(len(distances_px), len(frames), len(distances_px_smooth))

plt.plot(
    frames[:min_length], distances_px[:min_length], "-", markersize=0.75, color="black"
)

plt.plot(
    frames[:min_length],
    distances_px_smooth[:min_length],
    "-",
    markersize=0.75,
    color="green",
    alpha=0.5,
)

plt.title("Pixel Distance vs.Frames")
plt.xlabel("Frames")
plt.ylabel("Pixel Distance")

plot_output_path = os.path.join(output_directory, "aa_video_plot_image.png")
plt.savefig(plot_output_path)

plt.show()

cap.release()
cv.destroyAllWindows()
