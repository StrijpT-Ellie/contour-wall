import cv2 as cv
import mediapipe as mp
import numpy as np

import argparse
import os

# Parser creation in case arguments need to be passed to make working with the script easier and more accessible
parser = argparse.ArgumentParser(
    description="Script to process images and correct the heigh of a person based on their distance from the camera using previously implemented depth estimation."
)

parser.add_argument(
    "--dir",
    type=str,
    default="no_floor_crops/",
    help="Directory from and to which to read and write images.",
)

args = parser.parse_args()

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

files = os.listdir("../../sauce/" + args.dir)

images_native = [file for file in files if file.lower().endswith(".jpg")]

with mpPose.Pose(static_image_mode=True) as pose:
    i = 0
    print()
    for image_file in images_native:
        image_path = os.path.join("../../sauce/" + args.dir, image_file)
        image = cv.imread(image_path)
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        height, width, channels = image.shape
        width = int(width / 5)
        height = int(height / 5)

        if results.pose_landmarks:
            print(f"INFO: landmarks found for images_native[{i}]")
            landmark = results.pose_landmarks.landmark
            mpDraw.draw_landmarks(
                image, results.pose_landmarks, mpPose.POSE_CONNECTIONS
            )

            shoulder_coords = (
                int((landmark[12].x + landmark[11].x) * image.shape[1] / 2),
                int((landmark[12].y + landmark[11].y) * image.shape[0] / 2),
            )

            hip_coords = (
                int((landmark[24].x + landmark[23].x) * image.shape[1] / 2),
                int((landmark[24].y + landmark[23].y) * image.shape[0] / 2),
            )

            heel_coords = (
                int((landmark[30].x + landmark[29].x) * image.shape[1] / 2),
                int((landmark[30].y + landmark[29].y) * image.shape[0] / 2),
            )

            cv.line(image, shoulder_coords, hip_coords, (0, 255, 0), 20)
            cv.line(image, shoulder_coords, heel_coords, (255, 0, 0), 20)

            shoulder_hip_distance_px = np.sqrt(
                (hip_coords[0] - shoulder_coords[0]) ** 2
                + (hip_coords[1] - shoulder_coords[1]) ** 2
            )

            shoulder_heels_distance_px = np.sqrt(
                (heel_coords[0] - shoulder_coords[0]) ** 2
                + (heel_coords[1] - shoulder_coords[1]) ** 2
            )

            print(
                f"INFO: measured pixel distance [shoulders -> hips]:  [{shoulder_hip_distance_px}]"
            )
            print(
                f"INFO: measured pixel distance [shoulders -> heels]: [{shoulder_heels_distance_px}]"
            )
        else:
            print(f"ERROR: landmarks not found for images_native[{i}]")

        # Indicator line text put in each image
        cv.putText(
            image,
            "indicator_line",
            (50, 100),
            cv.FONT_HERSHEY_PLAIN,
            5,
            (0, 0, 0),
            5,
        )

        # Indicato line drawn into each image, based on the size of the shoulder -> heels distance in pixels
        cv.line(image, (350, 200), (350, image.shape[0]), (0, 0, 255), 20)
        cv.imshow(
            f"image[{i}]",
            cv.resize(
                image,
                (width, height),
                interpolation=cv.INTER_LINEAR,
            ),
        )
        cv.moveWindow(f"image[{i}]", width * i, 0)
        print()
        i += 1

cv.waitKey(0)
