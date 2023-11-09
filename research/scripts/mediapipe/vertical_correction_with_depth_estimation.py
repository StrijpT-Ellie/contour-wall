import cv2 as cv
import mediapipe as mp
import numpy as np
import time

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

cap = cv.VideoCapture("../../sauce/unused/final_location/honza_400_150_50/honza_400_100_50_increments.mp4")

previous_time = 0

def calculateFactor(pixel_distance):
    return (-0.012 * pixel_distance + 3.73)

def defineBoundingBox(image_landmarks, width, height):
    x_landmarks = []
    y_landmarks = []

    for processed_landmark in image_landmarks:
        x_landmarks.append(processed_landmark.x)
        y_landmarks.append(processed_landmark.y)

    x_max = int((max(x_landmarks) * width))
    y_max = int((max(y_landmarks) * height))
    x_min = int((min(x_landmarks) * width))
    y_min = int((min(y_landmarks) * height))

    start_point = (x_min, y_min)
    end_point = (x_max, y_max)

    return (start_point, end_point)

def calculateDistanceShoulderNose(landmarks, img):

    shoulder_coords = (
        int((landmarks[12].x + landmarks[11].x) * img.shape[1] / 2),
        int((landmarks[12].y + landmarks[11].y) * img.shape[0] / 2),
    )

    hips_coorde = (
        int((landmarks[24].x + landmarks[23].x) * img.shape[1] / 2),
        int((landmarks[24].y + landmarks[23].y) * img.shape[0] / 2),
    )
    # nose_coords = (
    #     int(landmarks[0].x * img.shape[1]),
    #     int(landmarks[0].y * img.shape[0]),
    # )

    return np.sqrt(
        (hips_coorde[0] - shoulder_coords[0]) ** 2
        + (hips_coorde[1] - shoulder_coords[1]) ** 2
    )

with mpPose.Pose(model_complexity=1) as pose:
    while cap.isOpened():
        ret, img = cap.read()

        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

        if not ret:
            break

        height, width, _ = img.shape
        height = int(height)
        width = int(width)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            # mpDraw.draw_landmarks(img, results.pose_landmarks.landmark, mpPose.POSE_CONNECTIONS)


            # print(f"bounding box: " + str(defineBoundingBox(landmarks, width, height)))

            points = defineBoundingBox(landmarks, width, height)

            # print(f"first point:" + str(points[0][1]))

            cropped_img = img[points[0][1]: points[1][1], points[0][0]: points[1][0]]

            cropped_height, cropped_width, _ = cropped_img.shape
            cropped_height = int(cropped_height)
            cropped_width = int(cropped_width)

            distance_px = calculateDistanceShoulderNose(landmarks, img)

            print("Distance: " + str(distance_px))

            cropped_img_upscale = cv.resize(
                cropped_img,
                (int(cropped_width * calculateFactor(distance_px)), int(cropped_height * calculateFactor(distance_px))),
                interpolation=cv.INTER_LINEAR,
            )

            cv.imshow("cropped_upscale", cropped_img_upscale)
            cv.imshow("image", img)

            cv.namedWindow("cropped_upscale", cv.WINDOW_NORMAL)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv.destroyAllWindows()