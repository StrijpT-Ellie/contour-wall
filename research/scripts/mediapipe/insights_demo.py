import cv2
import mediapipe as mp
import math
import numpy as np

def calculate_hue_angle(x, y):
    angle = math.degrees(math.atan2(y, x))
    return (angle + 180) % 360  # Normalize to the range [0, 360]

def interpolate_color(angle):
    # Interpolate between red, green, and blue based on the angle
    if 0 <= angle < 120:
        return (0, int(255 * (1 - angle / 120)), int(255 * (angle / 120)))
    elif 120 <= angle < 240:
        return (int(255 * ((angle - 120) / 120)), 0, int(255 * (1 - (angle - 120) / 120)))
    else:
        return (int(255 * (1 - (angle - 240) / 120)), int(255 * ((angle - 240) / 120)), 0)

def draw_palm_box(frame, palm_landmarks, scale_factor=1.5, output_size=(20, 20), upscale_factor=10):
    # Get coordinates of specific landmarks
    landmarks_indices = [0, 1, 2, 5, 9, 13, 17]
    landmarks_coordinates = [(int(palm_landmarks[i].x * width), int(palm_landmarks[i].y * height)) for i in landmarks_indices]

    # Calculate the average coordinates of the specified landmarks
    avg_x = int(sum(coord[0] for coord in landmarks_coordinates) / len(landmarks_coordinates))
    avg_y = int(sum(coord[1] for coord in landmarks_coordinates) / len(landmarks_coordinates))

    # Calculate bounding box parameters and apply the scale factor
    w = int(max(coord[0] for coord in landmarks_coordinates) - min(coord[0] for coord in landmarks_coordinates)) * scale_factor
    h = int(max(coord[1] for coord in landmarks_coordinates) - min(coord[1] for coord in landmarks_coordinates)) * scale_factor

    # Calculate hue based on hand orientation
    hue_angle = calculate_hue_angle(palm_landmarks[9].x - palm_landmarks[5].x, palm_landmarks[9].y - palm_landmarks[5].y)

    # Interpolate color based on hue angle
    color = interpolate_color(hue_angle)

    # Create a black background image with the same size as the input frame
    black_frame = np.zeros_like(frame)

    # Draw a filled oval (ellipse) around the center of the palm on the black background
    cv2.ellipse(black_frame, ((avg_x, avg_y), (w, h), 0), color, -1)

    # Resize the black frame to the desired output size
    black_frame_resized = cv2.resize(black_frame, output_size, interpolation=cv2.INTER_AREA)

    # Upscale the image
    upscaled_frame = cv2.resize(black_frame_resized, (output_size[0] * upscale_factor, output_size[1] * upscale_factor), interpolation=cv2.INTER_NEAREST)

    return upscaled_frame

def hand_tracking():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()

    # OpenCV setup
    cap = cv2.VideoCapture(0)
    global width, height
    width, height = 640, 480
    cap.set(3, width)
    cap.set(4, height)

    while True:
        ret, frame = cap.read()

        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                upscaled_frame = draw_palm_box(frame, hand_landmarks.landmark, output_size=(20, 20), upscale_factor=100)
                cv2.imshow("Hand Tracking", upscaled_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release
    cap.release()
    cv2.destroyAllWindows()

hand_tracking()