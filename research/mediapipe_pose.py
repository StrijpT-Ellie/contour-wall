import sys
import time
import math

import cv2 as cv
import cvzone as cvz
import mediapipe as mp
import numpy as np

WIDTH = 1280
HEIGHT = 960



def pythagoras_normalized(landmarkA, landmarkB):
    return math.sqrt(
        (landmarkA.x - landmarkB.x) ** 2
        + (landmarkA.y - landmarkB.y) ** 2
    )

def drawLine(landmarkA, landmarkB, frame, wideBoyFactor, hex="FFFFFF"):
    cv.line(
        frame,
        (int(landmarkA.x), int(landmarkA.y)),
        (int(landmarkB.x), int(landmarkB.y)),
        (tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))),
        int(
            math.ceil(
                pythagoras_normalized(landmarkA, landmarkB)
                / wideBoyFactor
            )
        ),
    )

def estimate_pose(cam_or_vid: str):
    blackBg = np.zeros((HEIGHT, WIDTH, 3), dtype = np.uint8)
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    previous_frame_time = 0

    cap = cv.VideoCapture(0) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid)
    pose = mp_pose.Pose(
        min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0
    )

    while True:
        # Get frame from vid or webcam
        _, frame = cap.read()

        frame = cv.resize(frame, (WIDTH, HEIGHT))

        cv.rectangle(blackBg, (0, 0), (WIDTH-1, HEIGHT-1), (0, 0, 0), -1)

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        frame.flags.writeable = False
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(frame)

        # Draw the pose annotation on the image.
        frame.flags.writeable = True
        frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

        for landmark in results.pose_landmarks.landmark:
            landmark.x, landmark.y = landmark.x * WIDTH, landmark.y * HEIGHT

        leftEyeInner = results.pose_landmarks.landmark[1]
        leftMouth = results.pose_landmarks.landmark[9]
        leftShoulder = results.pose_landmarks.landmark[11]
        leftElbow = results.pose_landmarks.landmark[13]
        leftWrist = results.pose_landmarks.landmark[15]
        leftHip = results.pose_landmarks.landmark[23]
        leftKnee = results.pose_landmarks.landmark[25]
        leftAnkle = results.pose_landmarks.landmark[27]

        rightEyeInner = results.pose_landmarks.landmark[4]
        rightMouth = results.pose_landmarks.landmark[10]
        rightShoulder = results.pose_landmarks.landmark[12]
        rightElbow = results.pose_landmarks.landmark[14]
        rightWrist = results.pose_landmarks.landmark[16]
        rightHip = results.pose_landmarks.landmark[24]
        rightKnee = results.pose_landmarks.landmark[26]
        rightAnkle = results.pose_landmarks.landmark[28]

        chestPts = np.array(
            [
                [rightShoulder.x, rightShoulder.y],
                [leftShoulder.x, leftShoulder.y],
                [leftHip.x, leftHip.y],
                [rightHip.x, rightHip.y],
            ],
            np.int32,
        )

        chestPts = chestPts.reshape((-1, 1, 2))

        neckPts = np.array(
            [
                [rightShoulder.x, rightShoulder.y],
                [leftShoulder.x, leftShoulder.y],
                [leftMouth.x, leftMouth.y],
                [rightMouth.x, rightMouth.y],
            ],
            np.int32,
        )

        neckPts = neckPts.reshape((-1, 1, 2))

        # Calculate the FPS of the output video
        cTime = time.time()
        fps = 1 / (cTime - previous_frame_time)
        previous_frame_time = cTime

        cv.putText(
            blackBg, str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3
        )

        # Fill neck and chest based on landmarks
        cv.fillPoly(blackBg, [chestPts], color=(255, 255, 255))
        cv.fillPoly(blackBg, [neckPts], color=(255, 255, 255))

        # Elipse drawing over the head based on the middle point between eyes
        cv.ellipse(
            blackBg,
            (int((rightEyeInner.x + leftEyeInner.x)/2),
               int((rightEyeInner.y + leftEyeInner.y)/2)),
              (int(pythagoras_normalized(rightShoulder, leftShoulder)*0.3),
               int(pythagoras_normalized(rightShoulder, leftShoulder)*0.45)),
               0,
               0,
               360,
               (255, 255, 255),
               -1
            )

        # shoulders
        drawLine(leftShoulder, rightShoulder, blackBg, 7)

        # hips
        drawLine(leftHip, rightHip, blackBg, 7)

        # left mouth > left shoulder
        drawLine(leftMouth, leftShoulder, blackBg, 8 )

        # left shoulder > left elbow
        drawLine(leftShoulder, leftElbow, blackBg, 3.8)

        # left elbow > left wrist
        drawLine(leftElbow, leftWrist, blackBg, 5)

        # left hip > left knee
        drawLine(leftHip, leftKnee, blackBg, 3)

        # left knee > left ankle
        drawLine(leftKnee, leftAnkle, blackBg, 3.5)

        # right shoulder > right elbow
        drawLine(rightShoulder, rightElbow, blackBg, 3.8)

        # right elbow > right wrist
        drawLine(rightElbow, rightWrist, blackBg, 5)

        # right shoulder > right hip
        drawLine(rightShoulder, rightHip, blackBg, 7)

        # right hip > right knee
        drawLine(rightHip, rightKnee, blackBg, 3)

        # right knee > right ankle
        drawLine(rightKnee, rightAnkle, blackBg, 3.5)

        cv.imshow("Original feed", frame)
        cv.imshow("Extrapolated pose", blackBg)

        # Quit if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()

    estimate_pose(sys.argv[-1])
