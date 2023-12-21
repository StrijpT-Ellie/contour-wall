import cv2
import mediapipe as mp
import math
import numpy as np

def draw_palm_box(frame, palm_landmarks, scale_factor=1.5, current_color=(0, 255, 0)):
    # Get coordinates of specific landmarks
    landmarks_indices = [0, 1, 2, 5, 9, 13, 17]
    landmarks_coordinates = [(int(palm_landmarks[i].x * width), int(palm_landmarks[i].y * height)) for i in landmarks_indices]

    # Calculate the average coordinates of the specified landmarks
    avg_x = int(sum(coord[0] for coord in landmarks_coordinates) / len(landmarks_coordinates))
    avg_y = int(sum(coord[1] for coord in landmarks_coordinates) / len(landmarks_coordinates))

    index_finger_down = palm_landmarks[8].y > palm_landmarks[5].y
    middle_finger_down = palm_landmarks[12].y > palm_landmarks[9].y
    ring_finger_down = palm_landmarks[16].y > palm_landmarks[13].y

    # Calculate bounding box parameters and apply the scale factor
    w = int(max(coord[0] for coord in landmarks_coordinates) - min(coord[0] for coord in landmarks_coordinates)) * scale_factor
    h = int(max(coord[1] for coord in landmarks_coordinates) - min(coord[1] for coord in landmarks_coordinates)) * scale_factor

    # Change color based on finger positions
    if index_finger_down:
        current_color = (0, 0, 255)
    elif middle_finger_down:
        current_color = (255, 0, 0)
    elif ring_finger_down:
        current_color = (255, 255, 255)

    # Draw a filled ellipse around the center of the palm
    cv2.ellipse(frame, ((avg_x, avg_y), (w, h), 0), current_color, -1)

    return current_color

def hand_tracking():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()

    # OpenCV setup
    cap = cv2.VideoCapture(0)
    global width, height
    width, height = 640, 480

    blackBg = np.zeros((height, width, 3), dtype=np.uint8)
    cap.set(3, width)
    cap.set(4, height)

    current_color = (0, 255, 0)

    while True:
        ret, frame = cap.read()

        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2.rectangle(blackBg, (0, 0), (WIDTH - 1, HEIGHT - 1), (0, 0, 0), -1)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                current_color = draw_palm_box(blackBg, hand_landmarks.landmark, current_color=current_color)
                current_color = draw_palm_box(frame, hand_landmarks.landmark, current_color=current_color)

        cv2.imshow("Hand Tracking black", blackBg)
        cv2.imshow("Hand Tracking frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release
    cap.release()
    cv2.destroyAllWindows()

hand_tracking()
