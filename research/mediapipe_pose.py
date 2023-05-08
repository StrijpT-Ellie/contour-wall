import sys
import time

import cv2 as cv
import mediapipe as mp

WIDTH = 1280
HEIGHT = 960


def estimate_pose(cam_or_vid: str):
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
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

        landmark11 = results.pose_landmarks.landmark[11]
        landmark13 = results.pose_landmarks.landmark[13]

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

        cv.line(
            frame,
            (int(landmark11.x * WIDTH), int(landmark11.y * HEIGHT)),
            (int(landmark13.x * WIDTH), int(landmark13.y * HEIGHT)),
            (255, 255, 0),
            int(100 - 20 * (landmark11.z)),
        )

        print(
            (int(landmark11.x * WIDTH), int(landmark11.y * HEIGHT)),
            (int(landmark13.x * WIDTH), int(landmark13.y * HEIGHT)),
        )

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
