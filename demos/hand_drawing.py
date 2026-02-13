from contourwall import ContourWall
import cv2 as cv
import mediapipe as mp
import numpy as np
import time
import colorsys

def get_interpolated_color(start_time, cycle_duration):
    elapsed_time = time.time() - start_time
    fraction = (elapsed_time % cycle_duration) / cycle_duration
    r, g, b = colorsys.hsv_to_rgb(fraction, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

def draw_hand_circle(image, hand_landmarks, painting_color):
    global prev_center_x, prev_center_y
    h, w, c = image.shape
    x_min = w
    y_min = h
    x_max = y_max = 0
    for lm in hand_landmarks.landmark:
        x, y = int(lm.x * w), int(lm.y * h)
        if x < x_min:
            x_min = x
        if y < y_min:
            y_min = y
        if x > x_max:
            x_max = x
        if y > y_max:
            y_max = y
    
    # Calculate the center of the bounding box
    center_x = (x_min + x_max) // 2
    center_y = (y_min + y_max) // 2

    # Scale the coordinates to fit the 60x40 canvas
    scale_x = 60 / w
    scale_y = 40 / h
    center_x = int(center_x * scale_x)
    center_y = int(center_y * scale_y)

    # Draw the circle on the canvas, leaving a trace
    if prev_center_x is not None and prev_center_y is not None:
        cv.circle(cw.pixels, (prev_center_x, prev_center_y), 3, painting_color, -1)

    # Update the previous center position
    prev_center_x = center_x
    prev_center_y = center_y

if __name__ == "__main__":
    global cw
    cw = ContourWall()
    cw.new()

    cw.pixels[:] = 0, 0, 50
    cw.show()

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.4)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv.VideoCapture(1 , cv.CAP_DSHOW)

    # Variables for tracking the hand position
    prev_center_x = None
    prev_center_y = None

    # Variables for tracking two hands detection
    two_hands_start_time = None
    two_hands_duration = 5  # seconds

    # Variables for color cycling
    start_time = time.time()
    cycle_duration = 4  # seconds

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break

        # Flip the image horizontally for a later selfie-view display
        image = cv.flip(image, 1)
        # Convert the BGR image to RGB
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)

        # Process the image and detect hands
        result = hands.process(image_rgb)

        # Update the painting color
        painting_color = get_interpolated_color(start_time, cycle_duration)

        # Draw hand landmarks and circle with the interpolated color
        num_hands = 0
        if result.multi_hand_landmarks:
            num_hands = len(result.multi_hand_landmarks)
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                draw_hand_circle(image, hand_landmarks, painting_color)

        # Display the output
        cv.namedWindow('hand_tracker', cv.WINDOW_NORMAL)
        cv.resizeWindow('hand_tracker', 720, 480)
        cv.imshow('hand_tracker', image)
        
        # Update the ContourWall display
        cw.show()

        if cv.waitKey(1) & 0xFF == ord('q'):
            cw.pixels[:] = 0, 0, 0
            cw.show()
            break

    cap.release()
    cv.destroyAllWindows()
