import sys
import time
import math

import cv2 as cv
import mediapipe as mp

WIDTH = 1280
HEIGHT = 960


def drawLine(landmarkA, landmarkB, frame, hex, wideBoyFactor):
    cv.line(
        frame,
        (int(landmarkA.x * WIDTH), int(landmarkA.y * HEIGHT)),
        (int(landmarkB.x * WIDTH), int(landmarkB.y * HEIGHT)),
        (tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))),
        int(
            math.ceil(
                math.sqrt(
                    (landmarkA.x * WIDTH - landmarkB.x * WIDTH) ** 2
                    + (landmarkA.y * HEIGHT - landmarkB.y * HEIGHT) ** 2
                )
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

    cap = (
        cv.VideoCapture(0) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid)
    )
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

        leftShoulder = results.pose_landmarks.landmark[11]
        leftElbow = results.pose_landmarks.landmark[13]
        leftWrist = results.pose_landmarks.landmark[15]
        leftHip = results.pose_landmarks.landmark[23]
        leftKnee = results.pose_landmarks.landmark[25]
        leftAnkle = results.pose_landmarks.landmark[27]

        rightShoulder = results.pose_landmarks.landmark[12]
        rightElbow = results.pose_landmarks.landmark[14]
        rightWrist = results.pose_landmarks.landmark[16]
        rightHip = results.pose_landmarks.landmark[24]
        rightKnee = results.pose_landmarks.landmark[26]
        rightAnkle = results.pose_landmarks.landmark[28]

        for id, lm in enumerate(results.pose_landmarks.landmark):
            cx, cy = int(lm.x * WIDTH), int(lm.y * HEIGHT)
            # print(id, cx, cy)
            cv.circle(frame, (cx, cy), 10, (255, 143, 0), cv.FILLED)

        # Calculate the FPS of the output video
        cTime = time.time()
        fps = 1 / (cTime - previous_frame_time)
        previous_frame_time = cTime

        cv.putText(
            frame, str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3
        )

        # shoulders
        drawLine(leftShoulder, rightShoulder, frame, "006666", 7)

        # hips
        drawLine(leftHip, rightHip, frame, "FF3333", 7)

        # left shoulder > left elbow
        drawLine(leftShoulder, leftElbow, frame, "CC00CC", 3.8)

        # left elbow > left wrist
        drawLine(leftElbow, leftWrist, frame, "FF33FF", 5)

        # left shoulder > left hip
        drawLine(leftShoulder, leftHip, frame, "CC0000", 7)

        # left hip > left knee
        drawLine(leftHip, leftKnee, frame, "0000CC", 2.5)

        # left knee > left ankle
        drawLine(leftKnee, leftAnkle, frame, "6666FF", 3.5)

        # right shoulder > right elbow
        drawLine(rightShoulder, rightElbow, frame, "4D9900", 3.8)

        # right elbow > right wrist
        drawLine(rightElbow, rightWrist, frame, "80FF00", 5)

        # right shoulder > right hip
        drawLine(rightShoulder, rightHip, frame, "00CCCC", 7)

        # right hip > right knee
        drawLine(rightHip, rightKnee, frame, "CCCC00", 2.5)

        # right knee > right ankle
        drawLine(rightKnee, rightAnkle, frame, "FFFF33", 3.5)

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
