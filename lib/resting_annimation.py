import cv2
import numpy as np
import random
import time

# Settings
width, height = 20, 20
bg_color = (0, 0, 0)

# Initial circle parameters
circle_radius = 2
x = random.randint(circle_radius * 2, width - circle_radius * 2)
y = random.randint(circle_radius * 2, height - circle_radius * 2)
x_speed = random.uniform(0.075, 0.2) * random.choice([-1, 1])
y_speed = random.uniform(0.075, 0.2) * random.choice([-1, 1])


# cw = ContourWall("COM6")


def random_colour():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


# # Initial color
circle_color = random_colour()


def draw_bouncing_circle(frame, x, y, radius, color):
    cv2.circle(frame, (int(x), int(y)), radius, color, -1)


while True:
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    draw_bouncing_circle(frame, x, y, circle_radius, circle_color)
    cv2.imshow('DVD Corner', frame)

    # cw.pixels = frame
    # cw.show()

    # Bounce off the edges
    if (x + circle_radius >= width) or (x - circle_radius <= 0):
        x_speed = -x_speed
        circle_color = random_colour()

    if (y + circle_radius >= height) or (y - circle_radius <= 0):
        y_speed = -y_speed
        circle_color = random_colour()

    x += x_speed
    y += y_speed

    # Wait for a short time to control the animation speed
    time.sleep(0.01)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()