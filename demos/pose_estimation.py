import sys
import time
import math

import cv2 as cv
import mediapipe as mp
import numpy as np

WIDTH = 1280
HEIGHT = 720

def pythagoras_normalized(landmarkA, landmarkB):
    return math.sqrt(
        (landmarkA.x - landmarkB.x) ** 2
        + (landmarkA.y - landmarkB.y) ** 2
    )

def draw_line(landmarkA, landmarkB, frame, wideBoyFactor, hex="FFFFFF"):
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
    cap = cv.VideoCapture(0) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid)  #MacOS
    # cap = cv.VideoCapture(0, cv.CAP_DSHOW) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid, cv.CAP_DSHOW) #Windows
    pose = mp_pose.Pose(
        min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0
    )

    while True:
        _, frame = cap.read()

        w, h = (40, 30)

        frame = cv.resize(frame, (WIDTH, HEIGHT))

        frame = cv.flip(frame, 1)

        cv.rectangle(blackBg, (0, 0), (WIDTH-1, HEIGHT-1), (0, 0, 0), -1)

        frame.flags.writeable = False
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(frame)

        frame.flags.writeable = True
        frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

        try:
            for landmark in results.pose_landmarks.landmark:
                landmark.x, landmark.y = landmark.x * WIDTH, landmark.y * HEIGHT
                
            leftEyeInner = results.pose_landmarks.landmark[1]
            leftMouth = results.pose_landmarks.landmark[9]
            leftShoulder = results.pose_landmarks.landmark[11]
            leftElbow = results.pose_landmarks.landmark[13]
            leftWrist = results.pose_landmarks.landmark[15]
            leftIndex = results.pose_landmarks.landmark[19]
            leftHip = results.pose_landmarks.landmark[23]
            leftKnee = results.pose_landmarks.landmark[25]
            leftAnkle = results.pose_landmarks.landmark[27]
            rightEyeInner = results.pose_landmarks.landmark[4]
            rightMouth = results.pose_landmarks.landmark[10]
            rightShoulder = results.pose_landmarks.landmark[12]
            rightElbow = results.pose_landmarks.landmark[14]
            rightWrist = results.pose_landmarks.landmark[16]
            rightIndex = results.pose_landmarks.landmark[20]
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

            cTime = time.time()
            fps = 1 / (cTime - previous_frame_time)
            previous_frame_time = cTime

            cv.fillPoly(blackBg, [chestPts], color=(255, 255, 255))
            cv.fillPoly(blackBg, [neckPts], color=(255, 255, 255))

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
            
            cv.ellipse(
                blackBg,
                (int(leftWrist.x),
                 int(leftWrist.y)),
                (int(pythagoras_normalized(leftWrist, leftIndex)*0.75),
                int(pythagoras_normalized(leftWrist, leftIndex)*0.75)),
                0,
                0,
                360,
                (255, 255, 255),
                -1
                )
            
            cv.ellipse(
                blackBg,
                (int(rightWrist.x),
                 int(rightWrist.y)),
                (int(pythagoras_normalized(rightWrist, rightIndex)*0.75),
                int(pythagoras_normalized(rightWrist, rightIndex)*0.75)),
                0,
                0,
                360,
                (255, 255, 255),
                -1
                )

            draw_line(leftShoulder, rightShoulder, blackBg, 7)

            draw_line(leftHip, rightHip, blackBg, 7)

            draw_line(leftShoulder, leftElbow, blackBg, 3.8)

            draw_line(leftElbow, leftWrist, blackBg, 5)

            draw_line(leftShoulder, leftHip, blackBg, 6.5)

            draw_line(leftHip, leftKnee, blackBg, 3)

            draw_line(leftKnee, leftAnkle, blackBg, 3.5)

            draw_line(rightShoulder, rightElbow, blackBg, 3.8)

            draw_line(rightElbow, rightWrist, blackBg, 5)

            draw_line(rightShoulder, rightHip, blackBg, 6.5)

            draw_line(rightHip, rightKnee, blackBg, 3)

            draw_line(rightKnee, rightAnkle, blackBg, 3.5)

            pixelBlackBg = cv.resize(blackBg, (w, h), interpolation=cv.INTER_LINEAR)

            pixelBlackBg = cv.resize(pixelBlackBg, (WIDTH, HEIGHT), interpolation=cv.INTER_NEAREST)

            cv.putText(
                blackBg, "fps: " + str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3
            )

            cv.imshow("Extrapolated pose", blackBg)

            cv.imshow("Extrapolated pose pixelated", pixelBlackBg)

            if cv.waitKey(1) & 0xFF == ord("q"):
                break
        
        except: 
            print("sum ting wong")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()

    estimate_pose(sys.argv[-1])
