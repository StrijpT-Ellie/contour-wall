import numpy as np
import cv2

video_capture_0 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
video_capture_1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
# video_capture_2 = cv2.VideoCapture(2)
# video_capture_3 = cv2.VideoCapture(3)

while True:
    ret0, frame0 = video_capture_0.read()
    ret1, frame1 = video_capture_1.read()
    # ret2, frame2 = video_capture_2.read()
    # ret3, frame3 = video_capture_3.read()

    if (ret0):
        cv2.imshow('cam_r', frame0)

    if (ret1):
        cv2.imshow('cam_l', frame1)

    # if (ret2):
    #     cv2.imshow('Cam 2', frame2)

    # if (ret3):
        # cv2.imshow('Cam 3', frame3)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture_0.release()
video_capture_1.release()
# video_capture_2.release()
# video_capture_3.release()
cv2.destroyAllWindows()