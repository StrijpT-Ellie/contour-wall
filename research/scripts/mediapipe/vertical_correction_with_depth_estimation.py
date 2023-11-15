import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import argparse
import pose_estimation

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

previous_time = 0

# Formula derived from plotting the points of the average relation between distance in pixels on the screen and real distance in centimeters of the subject from the camera
def getFactor(pixel_distance):
    return abs(-0.015 * pixel_distance + 3.73)

# Defines the bounding box coordinates (start_point, end_point) that are later used to crop the frame so it still contains the subject but no other subjects
def getBoundingPoints(image_landmarks, width, height):
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

# Calculates the distance in pixels on the screen between the shoulder and hip landmarks
def getPixelDistance(landmarks, img):

    shoulder_coords = (
        int((landmarks[12].x + landmarks[11].x) * img.shape[1] / 2),
        int((landmarks[12].y + landmarks[11].y) * img.shape[0] / 2),
    )

    hips_coorde = (
        int((landmarks[24].x + landmarks[23].x) * img.shape[1] / 2),
        int((landmarks[24].y + landmarks[23].y) * img.shape[0] / 2),
    )

    return np.sqrt(
        (hips_coorde[0] - shoulder_coords[0]) ** 2
        + (hips_coorde[1] - shoulder_coords[1]) ** 2
    )

# Corrects the image size based on the pixel distance calculated
def correctImageSize(img, cropped_width, cropped_height, scale_factor):
    return cv.resize(
        img,
        (int(cropped_width * scale_factor), int(cropped_height * scale_factor)),
        interpolation=cv.INTER_LINEAR
        
    )

# Argument parsing
parser = argparse.ArgumentParser(description="Pose estimation and image processing script.")
parser.add_argument("--video", action="store_true")
parser.add_argument("--webcam", action="store_true")
args = parser.parse_args()

if args.webcam:
    cap = cv.VideoCapture(0, cv.CAP_DSHOW)
    print("readin webcam")
else:
    cap = cv.VideoCapture("../../sauce/final_location/honza_400_150_50_cropped/honza_400_100_50_increments.mp4")
    print("reading video")

# Initialize pose object
with mpPose.Pose(model_complexity=1) as pose:
    # While video is being read
    while cap.isOpened():
        ret, img = cap.read()
        imgRGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        results = pose.process(imgRGB)

        # If video is not being read, break loop
        if not ret:
            break

        # Read and convert native image's height and width to integer values
        height, width, _ = img.shape
        height = int(height)
        width = int(width)

        # If landmarks on the pose are detected, continue
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Calculate the bounding/cropping box coordinates based on the current frame and identified landmarks
            points = getBoundingPoints(landmarks, width, height)

            # Crop image based on calculated coordinates
            cropped_img = img[points[0][1]: points[1][1], points[0][0]: points[1][0]]

            # Read and convert cropped image's height and width to integer values
            cropped_height, cropped_width, _ = cropped_img.shape
            cropped_height = int(cropped_height)
            cropped_width = int(cropped_width)

            # Calculate the pixel distance between the landmakrs for a given image
            distance_px = getPixelDistance(landmarks, img)

            # Calculate the scaling factor for the given image
            scaling_factor = getFactor(distance_px)

            # Crop image based on the pixel distance and scaling_factor calculated before for a given frame
            cropped_img_upscale = correctImageSize(cropped_img, cropped_width, cropped_height, scaling_factor)

            cv.imshow("cropped_upscale", cropped_img_upscale)

            cv.namedWindow("cropped_upscale", cv.WINDOW_NORMAL)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv.destroyAllWindows()