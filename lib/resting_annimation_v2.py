import cv2
import numpy as np
import random

from contourwall import ContourWall

# Initialize parameters
width, height = 100, 100
ball_radius = 12
ball_pos = [width // 2, height // 2]
ball_base_speed = 2
ball_speed = [random.randint(-ball_base_speed, ball_base_speed), random.randint(-ball_base_speed, ball_base_speed)]
angle_factor = 0.2

# Function to update ball position and speed
def update_ball():
    ball_pos, ball_speed, ball_color

    # Update position
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    # Check for collisions and update speed and angle
    if ball_pos[0] <= ball_radius or ball_pos[0] >= width - ball_radius:
        ball_speed[0] = -ball_speed[0]
        ball_speed[1] += random.uniform(-angle_factor, angle_factor)  # Adjust angle
        ball_color = get_random_color()
    if ball_pos[1] <= ball_radius or ball_pos[1] >= height - ball_radius:
        ball_speed[1] = -ball_speed[1]
        ball_speed[0] += random.uniform(-angle_factor, angle_factor)  # Adjust angle    
        ball_color = get_random_color()

def get_random_color():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

ball_color = get_random_color()

# Create a window
cv2.namedWindow('Bouncing Ball')

# cw = ContourWall("COM6")

while True:
    # Create a black image
    black_image = np.zeros((height, width, 3), dtype=np.uint8)

    # Update and draw the ball
    update_ball()
    cv2.circle(black_image, (int(ball_pos[0]), int(ball_pos[1])), ball_radius, ball_color, -1)

    # Display the image
    output_size = (20, 20)
    upscale_factor = 50
    black_image2 = cv2.resize(black_image, output_size, cv2.INTER_AREA)
    black_image3 = cv2.resize(black_image2, (output_size[0] * upscale_factor, output_size[1] * upscale_factor),
                                interpolation=cv2.INTER_NEAREST)
    cv2.imshow('Bouncing Ball', black_image3)
    # cw.pixels = black_image
    # cw.show()

    # Break loop with ESC key
    if cv2.waitKey(10) == 27:
        break

cv2.destroyAllWindows()
