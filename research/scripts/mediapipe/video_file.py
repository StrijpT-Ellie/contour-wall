import os
import cv2 as cv
import mediapipe as mp
import time
import matplotlib.pyplot as plt
import numpy as np

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
# pose = mpPose.Pose()

cap = cv.VideoCapture("../../sauce/tara_400cm_100cm.mp4")

pTime = 0

width = 640
height = 480
dimensions = (width, height)

with mpPose.Pose(
      model_complexity=1,
      ) as pose:
    while cap.isOpened():


        _, img = cap.read()
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

        # if results.pose_landmarks:
        #     mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        if results.pose_landmarks:
            mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

            # Get the landmark indices for the shoulders and nose
            shoulder_landmark = mpPose.PoseLandmark.RIGHT_SHOULDER
            nose_landmark = mpPose.PoseLandmark.NOSE

            # Get the coordinates for the shoulders and nose landmarks
            shoulder_coords = (
                int(
                    (
                        results.pose_landmarks.landmark[12]
                        .x
                        + results.pose_landmarks.landmark[11]
                        .x
                    )
                    * img.shape[1]
                    / 2
                ),
                int(
                    (
                        results.pose_landmarks.landmark[12]
                        .y
                        + results.pose_landmarks.landmark[11]
                        .y
                    )
                    * img.shape[0]
                    / 2
                ),
            )
            nose_coords = (
                int(results.pose_landmarks.landmark[0].x * img.shape[1]),
                int(results.pose_landmarks.landmark[0].y * img.shape[0]),
            )

            # Draw a line from the center of the shoulders to the nose
            cv.line(img, shoulder_coords, nose_coords, (0, 255, 0), 3)

            pixel_distance = np.sqrt(
                (nose_coords[0] - shoulder_coords[0]) ** 2
                + (nose_coords[1] - shoulder_coords[1]) ** 2
            )
            cv.putText(img, str(int(pixel_distance)), (70, 100), cv.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv.putText(img, str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        cv.imshow('image', img)

        if cv.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()