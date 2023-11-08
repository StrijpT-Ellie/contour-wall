import cv2 as cv
import mediapipe as mp
import numpy as np
import time

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

factor = 1.2

cap = cv.VideoCapture("../../sauce/unused/final_location/tara_400_150_50/tara_400_100_50_increments.mp4")

previous_time = 0

with mpPose.Pose(model_complexity=1) as pose:
    while cap.isOpened():
        ret, img = cap.read()

        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)
        landmark = results.pose_landmarks.landmark

        if not ret:
            break

        height, width, _ = img.shape
        height = int(height)
        width = int(width)

        x_landmarks = []
        y_landmarks = []

        if results.pose_landmarks:
            mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
            for landmark in results.pose_landmarks.landmark:
                x_landmarks.append(landmark.x)
                y_landmarks.append(landmark.y)

            x_max = int((max(x_landmarks) * width))
            y_max = int((max(y_landmarks) * height))
            x_min = int((min(x_landmarks) * width))
            y_min = int((min(y_landmarks) * height))

            cv.circle(img, (x_max, y_max), 3, (0, 255, 0), 3)
            cv.circle(img, (x_min, y_min), 3, (255, 0, 0), 3)
            start_point = (x_max, y_max)
            end_point = (x_min, y_min)
            cv.rectangle(img, start_point, end_point, (0, 0, 0), 3)

            cropped_img = img[y_min:y_max, x_min:x_max]

            c_height, c_width, _ = cropped_img.shape
            cv.imshow("cropped_original", cropped_img)

            cropped_img_upscale = cv.resize(
                cropped_img,
                (int(c_width * factor), int(c_height * factor)),
                interpolation=cv.INTER_LINEAR,
            )

            cv.imshow("cropped_upscale", cropped_img_upscale)
            cv.imshow("image", img)

            cu_height, cu_width, _ = cropped_img_upscale.shape

            bordered_img = cv.copyMakeBorder(
                cropped_img_upscale,
                top=height - cu_height,
                bottom=0,
                left=int((width - cu_width) / 2),
                right=int((width - cu_width) / 2),
                borderType=cv.BORDER_CONSTANT,
                value=[0, 0, 0],
            )

            current_time = time.time()
            fps = 1 / (current_time - previous_time)
            previous_time = current_time

            cv.putText(
                bordered_img,
                "FPS: " + str(int(fps)),
                (50, 50),
                cv.FONT_HERSHEY_PLAIN,
                3,
                (255, 255, 255),
                3,
            )

            cv.imshow("border", bordered_img)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv.destroyAllWindows()