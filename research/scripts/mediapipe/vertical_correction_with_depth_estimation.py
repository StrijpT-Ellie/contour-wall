import cv2 as cv
import mediapipe as mp
import numpy as np
import argparse
import math

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

previous_time = 0


# Formula derived from plotting the points of the average relation between distance in pixels on the screen and real distance in centimeters of the subject from the camera
def getFactor(pixel_distance):
    return abs(-0.006 * pixel_distance + 2.1)

# Defines the bounding box coordinates (start_point, end_point) that are later used to crop the frame so it still contains the subject but no other subjects
def getBoundingPoints(image_landmarks, width, height):
    x_landmarks = []
    y_landmarks = []

    for processed_landmark in image_landmarks:
        x_landmarks.append(processed_landmark.x)
        y_landmarks.append(processed_landmark.y)

    x_max = int((max(x_landmarks) * width) + (width * 0.015))
    y_max = int((max(y_landmarks) * height) + (height * 0.01))
    x_min = int((min(x_landmarks) * width) - (width * 0.015))
    y_min = int((min(y_landmarks) * height) - (height * 0.035))

    start_point = (x_min, y_min)
    end_point = (x_max, y_max)

    return (start_point, end_point)


# Calculates the distance in pixels on the screen between the shoulder and hip landmarks
def getPixelDistance(landmarks, img):

    knee_coords = (
        int((landmarks[26].x + landmarks[25].x) * img.shape[1] / 2),
        int((landmarks[26].y + landmarks[25].y) * img.shape[0] / 2),
    )

    hips_coords = (
        int((landmarks[24].x + landmarks[23].x) * img.shape[1] / 2),
        int((landmarks[24].y + landmarks[23].y) * img.shape[0] / 2),
    )

    return np.sqrt(
        (hips_coords[0] - knee_coords[0]) ** 2
        + (hips_coords[1] - knee_coords[1]) ** 2
    )


# Corrects the image size based on the pixel distance calculated
def correctImageSize(img, cropped_width, cropped_height, scale_factor):
    return cv.resize(
        img,
        (int(cropped_width * scale_factor), int(cropped_height * scale_factor)),
        interpolation=cv.INTER_LINEAR,
    )


# Draws a line between two points onto a frame
def drawLine(img, landmark_a, landmark_b, width_multiplier):
    point_a = np.array([int(landmark_a.x * width), int(landmark_a.y * height)])
    point_b = np.array([int(landmark_b.x * width), int(landmark_b.y * height)])
    thickness = int(math.ceil(np.linalg.norm(point_a - point_b) / width_multiplier))
    cv.line(img, tuple(point_a), tuple(point_b), (255, 255, 255), thickness)


# Draws an ellipse based on an image and the center defined by a landmark
def drawEllipse(img, landmark, axes):
    cv.ellipse(
        img,
        (int(landmark.x * width), int(landmark.x * height)),
        axes,
        0,
        0,
        360,
        (255, 255, 255),
        -1,
    )


# Argument parsing
parser = argparse.ArgumentParser(
    description="Pose estimation and image processing script."
)
parser.add_argument("--webcam", action="store_true")
args = parser.parse_args()

if args.webcam:
    cap = cv.VideoCapture(0, cv.CAP_DSHOW)
    print("readin webcam")
else:
    cap = cv.VideoCapture(
        "../../sauce/final_location/honza_400_150_50_cropped/honza_400_100_50_increments.mp4"
    )
    print("reading video")

# Initialize pose object
with mpPose.Pose(model_complexity=0) as pose:
    # While video is being read
    while cap.isOpened():
        w, h = (43, 32)
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

        blackBg = np.zeros((height, width, 3), dtype=np.uint8)

        cv.rectangle(blackBg, (0, 0), (width - 1, height - 1), (0, 0, 0), -1)

        # If landmarks on the pose are detected, continue
        if results.pose_landmarks:
            mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            # Defining landmarks for drawing lines of the contour
            nose = results.pose_landmarks.landmark[0]

            leftMouth = results.pose_landmarks.landmark[9]
            leftShoulder = results.pose_landmarks.landmark[11]
            leftElbow = results.pose_landmarks.landmark[13]
            leftWrist = results.pose_landmarks.landmark[15]
            leftHip = results.pose_landmarks.landmark[23]
            leftKnee = results.pose_landmarks.landmark[25]
            leftAnkle = results.pose_landmarks.landmark[27]

            rightMouth = results.pose_landmarks.landmark[10]
            rightShoulder = results.pose_landmarks.landmark[12]
            rightElbow = results.pose_landmarks.landmark[14]
            rightWrist = results.pose_landmarks.landmark[16]
            rightHip = results.pose_landmarks.landmark[24]
            rightKnee = results.pose_landmarks.landmark[26]
            rightAnkle = results.pose_landmarks.landmark[28]

            chest_coordinates = np.array(
                [
                    [rightShoulder.x * width, rightShoulder.y * height],
                    [leftShoulder.x * width, leftShoulder.y * height],
                    [leftHip.x * width, leftHip.y * height],
                    [rightHip.x * width, rightHip.y * height],
                ],
                np.int32,
            )
            chest_coordinates = chest_coordinates.reshape((-1, 1, 2))

            hips_center = (
                int((leftHip.x * width + rightHip.x * width) / 2),
                int((leftHip.y * height + rightHip.y * height) / 2),
            )

            # neck
            start = (
                int((leftHip.x * width + rightHip.x * width) / 2),
                int((leftHip.y * height + rightHip.y * height) / 2),
            )
            end = (int(nose.x * width), int(nose.y * height))

            cv.ellipse(
                blackBg,
                (int(nose.x * width), int(nose.y * height)),
                (30, 40),
                0,
                0,
                360,
                (255, 255, 255),
                -1,
            )

            cv.ellipse(
                blackBg,
                (int(leftWrist.x * width), int(leftWrist.y * height)),
                (10, 15),
                0,
                0,
                360,
                (255, 255, 255),
                -1,
            )

            cv.ellipse(
                blackBg,
                (int(rightWrist.x * width), int(rightWrist.y * height)),
                (10, 15),
                0,
                0,
                360,
                (255, 255, 255),
                -1,
            )

            cv.line(blackBg, start, end, (255, 255, 255), 15)

            # chest
            cv.fillPoly(blackBg, [chest_coordinates], color=(255, 255, 255))

            # left shoulder > left elbow
            drawLine(blackBg, leftShoulder, leftElbow, 3.8)

            # left elbow > left wrist
            drawLine(blackBg, leftElbow, leftWrist, 5)

            # left hip > left knee
            drawLine(blackBg, leftHip, leftKnee, 4)

            # left knee > left ankle
            drawLine(blackBg, leftKnee, leftAnkle, 4.5)

            # right shoulder > right elbow
            drawLine(blackBg, rightShoulder, rightElbow, 3.8)

            # right elbow > right wrist
            drawLine(blackBg, rightElbow, rightWrist, 5)

            # right hip > right knee
            drawLine(blackBg, rightHip, rightKnee, 4)

            # right knee > right ankle
            drawLine(blackBg, rightKnee, rightAnkle, 4.5)

            #####################################################################################################################
            # CROPPING STARTS HERE
            # Calculate the bounding/cropping box coordinates based on the current frame and identified landmarks
            points = getBoundingPoints(landmarks, width, height)

            # Crop image based on calculated coordinates
            cropped_img = blackBg[
                points[0][1]: points[1][1], points[0][0]: points[1][0]
            ]

            # Read and convert cropped image's height and width to integer values
            cropped_height, cropped_width, _ = cropped_img.shape
            cropped_height = int(cropped_height)
            cropped_width = int(cropped_width)

            # Calculate the pixel distance between the landmakrs for a given image
            distance_px = getPixelDistance(landmarks, img)

            # Calculate the scaling factor for the given image
            scaling_factor = getFactor(distance_px)

            # Crop image based on the pixel distance and scaling_factor calculated before for a given frame
            cropped_img_upscale = correctImageSize(
                cropped_img, cropped_width, cropped_height, scaling_factor
            )

            cropped_img_upscale_height, _, _ = cropped_img_upscale.shape
            print(f"cropped img upscale height {str(cropped_img_upscale_height)}")

            pixelBlackBg = cv.resize(cropped_img_upscale, (w, h), interpolation=cv.INTER_LINEAR)

            pixelBlackBg = cv.resize(
                pixelBlackBg, (960, 1280), interpolation=cv.INTER_NEAREST
            )

            cv.putText(img, "factor: " + str(scaling_factor), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3)
            cv.putText(img, "distance_px: " + str(distance_px), (70, 150), cv.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3)

            # width_needed = ((width / 2) - (cropped_width / 2))

            # pixelBlackBg = cv.copyMakeBorder(
            #     pixelBlackBg,
            #     top=120,
            #     bottom=0,
            #     left=820,
            #     right=820,
            #     borderType=cv.BORDER_CONSTANT,
            #     value=[0, 0, 0],
            # )

            cv.imshow("native_image", img)
            cv.imshow("corrected_pixelated_image", pixelBlackBg)
            # cv.moveWindow("pixels wee", 0, 0)
            # cv.imshow("Native image", img)
            #
            # cv.imshow("Black background", blackBg)
            #
            # cv.imshow("Black background cropped", cropped_img_upscale)

        if cv.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv.destroyAllWindows()
