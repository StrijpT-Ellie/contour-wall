import cv2
import mediapipe as mp
import numpy as np
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib/wrappers/python"))
)

from contourwall_emulator import ContourWallEmulator, hsv_to_rgb

# Also changed from `ContourWall` to `ContourWallEmulator`
cw = ContourWallEmulator()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2, # Set the maximum number of hands that can be detected
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open webcam
cap = cv2.VideoCapture(1)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Flip for mirror effect and convert color
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Collect all landmark points
            h, w, _ = frame.shape
            points = np.array([
                [int(lm.x * w), int(lm.y * h)] 
                for lm in hand_landmarks.landmark
            ])

            # Get bounding ellipse
            if len(points) >= 5:  # need at least 5 points for fitEllipse
                ellipse = cv2.fitEllipse(points)
                cv2.ellipse(frame, ellipse, (0, 255, 0), 2)

    cv2.imshow("Hand Ellipse Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

cw.show()