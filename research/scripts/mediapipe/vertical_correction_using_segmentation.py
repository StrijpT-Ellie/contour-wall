import cv2 as cv
import mediapipe as mp
import numpy as np

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

x_landmarks = []
y_landmarks = []

factor = 2

img = cv.imread("../../sauce/no_floor_crops/tara_350.jpg")
img150 = cv.imread("../../sauce/no_floor_crops/tara_150.jpg")
height, width, _ = img.shape
height = int(height / 2)
width = int(width / 2)

with mpPose.Pose(static_image_mode=True, model_complexity=1) as pose:
    imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    results = pose.process(imgRGB)

    if results.pose_landmarks:
        mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
        for landmark in results.pose_landmarks.landmark:
            x_landmarks.append(landmark.x)
            y_landmarks.append(landmark.y)
    img = cv.resize(img, (width, height), cv.INTER_LINEAR)
    img150 = cv.resize(img150, (width, height), cv.INTER_LINEAR)

    # print(f"X landmarks: {x_landmarks}")
    # print()
    # print(f"Y landmarks: {y_landmarks}")

    x_max = int(max(x_landmarks) * width)
    y_max = int(max(y_landmarks) * height)
    x_min = int(min(x_landmarks) * width)
    y_min = int(min(y_landmarks) * height)

    print()

    print(f"x_max = {x_max}, x_min = {x_min}")
    print()
    print(f"y_max = {y_max}, y_min = {y_min}")

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
    cv.imshow("150", img150)
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

    cv.imshow("border", bordered_img)


cv.waitKey(0)
cv.destroyAllWindows()
