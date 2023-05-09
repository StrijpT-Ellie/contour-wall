import sys
import time
import math

import cv2 as cv
import mediapipe as mp
import numpy as np

WIDTH = 1280
HEIGHT = 960

def pythagoras_normalized(landmarkA, landmarkB):
    return math.sqrt(
        (landmarkA.x - landmarkB.x) ** 2
        + (landmarkA.y - landmarkB.y) ** 2
    )

def drawLine(landmarkA, landmarkB, frame, hex, wideBoyFactor):
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
    # mp_drawing = mp.solutions.drawing_utils
    # mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    previous_frame_time = 0

    cap = cv.VideoCapture(0) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid)
    # model_complexity improves performance, but only 2 is actually much slower
    pose = mp_pose.Pose(
        min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0
    )

    while True:
        # Get frame from vid or webcam
        _, frame = cap.read()

        frame = cv.resize(frame, (WIDTH, HEIGHT))

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        frame.flags.writeable = False
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(frame)

        # Draw the pose annotation on the image.
        frame.flags.writeable = True
        frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        # mp_drawing.draw_landmarks(
        #     frame,
        #     results.pose_landmarks,
        #     landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        # )

        for landmark in results.pose_landmarks.landmark:
            landmark.x, landmark.y = landmark.x * WIDTH, landmark.y * HEIGHT

        nose = results.pose_landmarks.landmark[0]

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

        cv.fillPoly(frame, [chestPts], color=(255, 255, 255))
        cv.fillPoly(frame, [neckPts], color=(255, 255, 255))

        cv.ellipse(
            frame,
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

        cv.putText(
            frame, str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3
        )

        # shoulders
        drawLine(leftShoulder, rightShoulder, frame, "FFFFFF", 7)

        # hips
        drawLine(leftHip, rightHip, frame, "FFFFFF", 7)

        # left mouth > left shoulder
        drawLine(leftMouth, leftShoulder, frame, "FFFFFF", 8 )

        # left shoulder > left elbow
        drawLine(leftShoulder, leftElbow, frame, "FFFFFF", 3.8)

        # left elbow > left wrist
        drawLine(leftElbow, leftWrist, frame, "FFFFFF", 5)

        # left hip > left knee
        drawLine(leftHip, leftKnee, frame, "FFFFFF", 3)

        # left knee > left ankle
        drawLine(leftKnee, leftAnkle, frame, "FFFFFF", 3.5)

        # right shoulder > right elbow
        drawLine(rightShoulder, rightElbow, frame, "FFFFFF", 3.8)

        # right elbow > right wrist
        drawLine(rightElbow, rightWrist, frame, "FFFFFF", 5)

        # right shoulder > right hip
        drawLine(rightShoulder, rightHip, frame, "FFFFFF", 7)

        # right hip > right knee
        drawLine(rightHip, rightKnee, frame, "FFFFFF", 3)

        # right knee > right ankle
        drawLine(rightKnee, rightAnkle, frame, "FFFFFF", 3.5)

        cv.imshow("MediaPipe Pose", frame)

        # Quit if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    print(sys.argv[-1])
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()

    estimate_pose(sys.argv[-1])
