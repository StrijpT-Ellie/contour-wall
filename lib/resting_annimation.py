import cv2
import numpy as np
import random
import time

# Settings
width, height = 640, 480
bg_color = (0, 0, 0)

# Initial circle parameters
circle_radius = 40
x = random.randint(circle_radius, width - circle_radius)
y = random.randint(circle_radius, height - circle_radius)
x_speed = 2.5
y_speed = 2.5

# # Initial color
circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def draw_bouncing_circle(frame, x, y, radius, color):
    cv2.circle(frame, (int(x), int(y)), radius, color, -1)


while True:
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    draw_bouncing_circle(frame, x, y, circle_radius, circle_color)
    cv2.imshow('DVD Corner', frame)

    # Bounce off the edges
    if (x + circle_radius >= width) or (x - circle_radius <= 0):
        x_speed = -x_speed
        circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    if (y + circle_radius >= height) or (y - circle_radius <= 0):
        y_speed = -y_speed
        circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    x += x_speed
    y += y_speed

    # Wait for a short time to control the animation speed
    time.sleep(0.01)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
