import cv2
import numpy as np
import random
import time

from contourwall import ContourWall

# Settings
width, height = 100, 100
background_color = (0, 0, 0)

# Initial circle parameters
circle_radius = 10
circle_position = [width // 2, height // 2]
circle_base_speed = 2
circle_speed = [random.randint(-circle_base_speed, circle_base_speed), random.randint(-circle_base_speed, circle_base_speed)]
angle_factor = 0.4

cw = ContourWall("COM6")

def get_random_color():
    # Define a list of 20 vibrant color tuples (in RGB format)
    colors = [
        (255, 0, 0),        # Red
        (0, 255, 0),        # Green
        (0, 0, 255),        # Blue
        (255, 255, 0),      # Yellow
        (255, 0, 255),      # Magenta
        (0, 255, 255),      # Cyan
        (255, 128, 0),      # Orange
        (255, 0, 127),      # Pink
        (128, 0, 255),      # Purple
        (0, 255, 128),      # Light Green
        (128, 255, 0),      # Lime
        (0, 128, 255),      # Light Blue
        (255, 128, 192),    # Peach
        (128, 255, 255),    # Aqua
        (255, 255, 128),    # Light Yellow
        (128, 128, 255),    # Lavender
        (255, 170, 170),    # Salmon Pink
        (170, 255, 170),    # Mint Green
        (170, 170, 255),    # Periwinkle
        (255, 216, 0)       # Gold
    ]

    # Randomly select and return one of the colors
    return random.choice(colors)

# Initialize circle color
circle_color = get_random_color()

# TODO: Make the circle a smiley face
def draw_circle(frame, x, y, radius, color):
    cv2.circle(frame, (int(x), int(y)), radius, color, -1)

def update_circle():
    global circle_position, circle_speed, circle_color

    circle_position[0] += circle_speed[0]
    circle_position[1] += circle_speed[1]

    # Bounce off the edges
    if circle_position[0] <= circle_radius or circle_position[0] >= width - circle_radius:
        circle_speed[0] = -circle_speed[0]
        circle_speed[1] += random.uniform(-angle_factor, angle_factor)
        circle_color = get_random_color()

    if circle_position[1] <= circle_radius or circle_position[1] >= height - circle_radius:
        circle_speed[1] = -circle_speed[1]
        circle_speed[0] += random.uniform(-angle_factor, angle_factor)
        circle_color = get_random_color()

    print(f"circle_speed_x [{circle_speed[0]}] circle_speed_y [{circle_speed[1]}]")

while True:
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Update and draw the circle
    update_circle()
    draw_circle(frame, circle_position[0], circle_position[1], circle_radius, circle_color)

    # Resize for pixelated effect
    output_size = (20, 20)
    upscale_factor = 1
    black_frame_resized = cv2.resize(frame, output_size, interpolation=cv2.INTER_AREA)
    upscaled_frame = cv2.resize(black_frame_resized, (output_size[0] * upscale_factor, output_size[1] * upscale_factor), interpolation=cv2.INTER_NEAREST)

    cw.pixels = upscaled_frame
    cw.show()

    # Display the frame
    cv2.imshow('Bouncing Circle', upscaled_frame)

    # Wait for a short time to control the animation speed
    time.sleep(0.01)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
