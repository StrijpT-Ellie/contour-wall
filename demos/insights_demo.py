# from contourwall import ContourWall
from contourwall_emulator import ContourWallEmulator, hsv_to_rgb

import cv2
import mediapipe as mp
import numpy as np
import time
import wave_rainbow as wr


width = 640
height = 480
RESTING_THRESHOLD = 5  # seconds before idle animation starts

# Connect to the Contour Wall
cw = ContourWall("COM6")


def calculate_hue_angle(x, y):
    """
    Calculate a hue angle (0–360) based on a 2D vector.
    Used to determine hand orientation.
    """
    return (np.degrees(np.arctan2(y, x)) + 180) % 360


def interpolate_color(angle):
    """
    Convert a hue angle (0–360) into an RGB color.
    This manually interpolates between red → green → blue.
    """
    if 0 <= angle < 120:
        return 0, int(255 * (1 - angle / 120)), int(255 * (angle / 120))
    elif 120 <= angle < 240:
        return int(255 * ((angle - 120) / 120)), 0, int(255 * (1 - (angle - 120) / 120))
    else:
        return int(255 * (1 - (angle - 240) / 120)), int(255 * ((angle - 240) / 120)), 0


def draw_palm_boxes(
    frame,
    hand_landmarks,
    scale_factor=1,
    output_size=(20, 20),
    upscale_factor=5,
    ellipse_size_factor=3
):
    """
    Draws filled ellipses around detected palms and
    returns a low-resolution frame for the Contour Wall.

    Steps:
    1. Create a black canvas
    2. Draw palm ellipses
    3. Downscale to wall resolution
    4. Upscale using nearest-neighbor (pixel look)
    """

    # Start with a black canvas (clears previous frame)
    canvas = np.zeros_like(frame)

    if hand_landmarks:
        for landmarks in hand_landmarks:

            # Palm-related landmark indices
            palm_indices = [0, 1, 2, 5, 9, 13, 17]

            # Convert normalized landmarks → pixel coordinates
            coords = np.array(
                [(landmarks[i].x * width, landmarks[i].y * height) for i in palm_indices],
                dtype=np.int32
            )

            # Get bounding box of the palm
            x, y, w, h = cv2.boundingRect(coords)
            w *= scale_factor
            h *= scale_factor

            # Calculate hand orientation (for color)
            hue_angle = calculate_hue_angle(
                landmarks[9].x - landmarks[5].x,
                landmarks[9].y - landmarks[5].y
            )

            color = interpolate_color(hue_angle)

            # Draw ellipse around palm
            cv2.ellipse(
                canvas,
                ((x + w // 2, y + h // 2), (w * ellipse_size_factor, h * ellipse_size_factor), 0),
                color,
                -1
            )

    # Downscale to Contour Wall resolution
    small = cv2.resize(canvas, output_size, interpolation=cv2.INTER_AREA)

    # Upscale for preview (keeps pixel look)
    upscaled = cv2.resize(
        small,
        (output_size[0] * upscale_factor, output_size[1] * upscale_factor),
        interpolation=cv2.INTER_NEAREST
    )

    return upscaled

def hand_tracking():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, width)
    cap.set(4, height)

    # Used to detect idle state
    last_hand_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks_list = [hand.landmark for hand in results.multi_hand_landmarks]

            frame_to_show = draw_palm_boxes(
                frame,
                hand_landmarks_list,
                output_size=(20, 20),
                upscale_factor=1
            )

            last_hand_time = time.time()

        else:
            if time.time() - last_hand_time >= RESTING_THRESHOLD:
                frame_to_show = wr.wave_rainbow()
            else:
                frame_to_show = draw_palm_boxes(frame, [], output_size=(20, 20), upscale_factor=1)

        cv2.imshow("Contour Wall Output", frame_to_show)

        # Send pixels to the Contour Wall
        cw.pixels = frame_to_show
        cw.show()

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

hand_tracking()
