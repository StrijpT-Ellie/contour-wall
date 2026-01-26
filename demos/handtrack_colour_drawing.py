import cv2
import mediapipe as mp
import numpy as np
import time
import colorsys
from contourwall import ContourWall, hsv_to_rgb

cw = ContourWall()
cw.new()

def hsv_to_rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s / 100.0, v / 100.0)
    return int(b * 255), int(g * 255), int(r * 255)

width = 1280
height = 720

def get_rainbow_color():
    hue = (time.time() * 60) % 360 #colour change speed can be set here
    return hsv_to_rgb(hue, 100, 100)

def draw_palm_box(canvas, palm_landmarks, scale_factor=1):
    if palm_landmarks:
        landmarks_indices = [0, 1, 2, 5, 9, 13, 17]
        landmarks_coordinates = np.array(
            [(palm_landmarks[i].x * width, palm_landmarks[i].y * height) for i in landmarks_indices],
            dtype=np.int32
        )

        x, y, w, h = cv2.boundingRect(landmarks_coordinates)
        w *= scale_factor
        h *= scale_factor

        ellipse = ((x + w // 2, y + h // 2), (w, h), 0)
        color = get_rainbow_color()
        cv2.ellipse(canvas, ellipse, color, -1)

def hand_tracking():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(1)
    cap.set(3, width)
    cap.set(4, height)

    trail = np.zeros((height, width, 3), dtype=np.uint8)
    fade = 0.97

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # Fade old pixels every frame
        trail = (trail * fade).astype(np.uint8)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                draw_palm_box(trail, hand_landmarks.landmark)

        cv2.imshow("Hand Tracking (Trails)", trail)
        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

hand_tracking()
