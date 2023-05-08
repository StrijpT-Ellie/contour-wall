import cv2
import mediapipe as mp
import time
import matplotlib.pyplot as plt

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

cap = cv2.VideoCapture("sauce/flop_2_480p.mp4")
# cap = cv2.VideoCapture(0)
pTime = 0

# while True:
#     _, img = cap.read()
#     # img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
#     imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

#     # imgRGB = cv2.resize(imgRGB, dim, interpolation = cv2.INTER_AREA)
#     results = pose.process(imgRGB)

#     if results.pose_landmarks:
#         mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

#     cTime = time.time()
#     fps = 1 / (cTime - pTime)
#     pTime = cTime

#     cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

#     cv2.imshow("image", img)

#     cv2.waitKey(10)

with mp_pose.Pose(
    min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=0
) as pose:
    while cap.isOpened():
        _, image = cap.read()

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        # Draw the pose annotation on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )

        # Flip the image horizontally for a selfie-view display.
        cv2.putText(
            image, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3
        )
        cv2.imshow("MediaPipe Pose", image)
        cv2.waitKey(10)
