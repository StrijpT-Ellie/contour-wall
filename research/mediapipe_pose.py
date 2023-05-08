import cv2
import mediapipe as mp
import time
import matplotlib.pyplot as plt

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
pose = mpPose.Pose()

cap = cv2.VideoCapture('sauce/flop_2.mp4')
pTime = 0

while True:
    _, img = cap.read()
    # img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # imgRGB = cv2.resize(imgRGB, dim, interpolation = cv2.INTER_AREA)
    results = pose.process(imgRGB)

    if results.pose_landmarks:
        mpDraw.draw_landmarks(img, results.pose_landmarks, mpPose.POSE_CONNECTIONS)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3,
               (255, 0, 0), 3)

    cv2.imshow('image', img)

    cv2.waitKey(10)