from contourwall import ContourWall

import cv2
import mediapipe as mp
import numpy as np
import time

width = 640
height = 480


def calculate_hue_angle(x, y):
    return (np.degrees(np.arctan2(y, x)) + 180) % 360


def interpolate_color(angle):
    # Interpolate between red, green, and blue based on the angle
    if 0 <= angle < 120:
        return 0, int(255 * (1 - angle / 120)), int(255 * (angle / 120))
    elif 120 <= angle < 240:
        return int(255 * ((angle - 120) / 120)), 0, int(255 * (1 - (angle - 120) / 120))
    else:
        return int(255 * (1 - (angle - 240) / 120)), int(255 * ((angle - 240) / 120)), 0


def draw_palm_boxes(frame, hand_landmarks, output_size=(20, 20), upscale_factor=1, ellipse_size_factor=50):
    """
        Function to draw palm boxes on the image.
        :param frame: input image
        :param hand_landmarks: list of hand landmarks
        :param output_size: size of the output image
        :param upscale_factor: factor to upscale the output image
        :param ellipse_size_factor: factor to upscale the ellipse at point 0 of the hand, base size is 3 wide 3 high
        :return: frame with palm boxes
    """

    black_frame = np.zeros_like(frame)

    if hand_landmarks:
        for landmarks in hand_landmarks:

            landmark_0 = (int(landmarks[0].x * width), int(landmarks[0].y * height))

            base_ellipse_size = (3, 3)
            scaled_ellipse_size = (
                int(base_ellipse_size[0] * ellipse_size_factor),
                int(base_ellipse_size[1] * ellipse_size_factor)
            )

            hue_angle = calculate_hue_angle(landmarks[9].x - landmarks[5].x, landmarks[9].y - landmarks[5].y)

            colour = interpolate_color(hue_angle)

            # Ellipse is drawn around 0 landmark so that it doesn't matter which orientation the hand is in
            # The colour is still calculated with other points and does matter
            # With this we hope to improve unseen points
            cv2.ellipse(black_frame, (landmark_0, scaled_ellipse_size, 0), colour, -1)

    black_frame_resized = cv2.resize(black_frame, output_size, interpolation=cv2.INTER_AREA)
    upscaled_frame = cv2.resize(black_frame_resized, (output_size[0] * upscale_factor, output_size[1] * upscale_factor),
                                interpolation=cv2.INTER_NEAREST)

    return upscaled_frame


def hand_tracking():
    previous_time = 0

    # cw = ContourWall("COM6")

    mp_hands = mp.solutions.hands
    # hands = mp_hands.Hands()

    # Can be used to increase the accuracy/speed, might be worth playing around with
    hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8, max_num_hands=2)

    # OpenCV setup
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, width)
    cap.set(4, height)

    while True:
        ret, frame = cap.read()

        frame = cv2.flip(frame, 1)
        # frame = cv2.flip(frame, 0)

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            hand_landmarks_list = [hand.landmark for hand in results.multi_hand_landmarks]
            frame_to_show = draw_palm_boxes(frame, hand_landmarks_list, output_size=(20, 20), upscale_factor=50)
        else:
            frame_to_show = draw_palm_boxes(frame, [], output_size=(20, 20), upscale_factor=50)

        cv2.imshow("Hand Tracking", frame_to_show)
        # cw.pixels = frame_to_show
        # cw.show()

        current_time = time.time()
        fps = 1 / (current_time - previous_time)
        previous_time = current_time

        cv2.putText(
            frame,
            str(int(fps)),
            (50, 100),
            cv2.FONT_HERSHEY_PLAIN,
            3,
            (0, 255, 0),
            3,
        )

        cv2.imshow("Hand", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release
    cap.release()
    cv2.destroyAllWindows()


hand_tracking()
