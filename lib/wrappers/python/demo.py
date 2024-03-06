from contourwall import ContourWall
import time
import sys

def hsv_to_rgb(h, s, v):
    h /= 255
    s /= 255
    v /= 255

    if s == 0.0:
        return int(v * 255), int(v * 255), int(v * 255)

    i = int(h * 6.)  # segment number (0 to 5)
    f = (h * 6.) - i  # fractional part of h
    p = v * (1. - s)
    q = v * (1. - s * f)
    t = v * (1. - s * (1. - f))

    if i == 0:
        return int(v * 255), int(t * 255), int(p * 255)
    elif i == 1:
        return int(q * 255), int(v * 255), int(p * 255)
    elif i == 2:
        return int(p * 255), int(v * 255), int(t * 255)
    elif i == 3:
        return int(p * 255), int(q * 255), int(v * 255)
    elif i == 4:
        return int(t * 255), int(p * 255), int(v * 255)
    else:
        return int(v * 255), int(p * 255), int(q * 255)

def test_flash_all_colors():
    # Set all pixels to RED
    cw.pixels[:] = 0, 0, 255
    cw.show()
    time.sleep(0.5)

    # Set all pixels to RED
    cw.pixels[:] = 0, 255, 255
    cw.show()
    time.sleep(0.5)

    # Set all pixels to GREEN
    cw.pixels[:] = 0, 255, 0
    cw.show()
    time.sleep(0.5)

    # Set all pixels to GREEN
    cw.pixels[:] = 255, 255, 0
    cw.show()
    time.sleep(0.5)

    # Set all pixels to BLUE
    cw.pixels[:] = 255, 0, 0
    cw.show()
    time.sleep(0.5)

    # Set all pixels to BLUE
    cw.pixels[:] = 255, 0, 255
    cw.show()
    time.sleep(0.5)

    # Set all pixels to WHITE
    cw.pixels[:] = 255, 255, 255
    cw.show()
    time.sleep(0.5)

    # Set all pixels to BLACK
    cw.pixels[:] = 0, 0, 0
    cw.show()
    time.sleep(0.5)

def test_fade_to_white():
    # Slowly fade to white
    for i in range(0, 255, 2):
        cw.pixels[:] =  i, i, i
        cw.show()
        time.sleep(0.025)
    cw.pixels[:] = 0, 0, 0
    cw.show()

def test_fade_colors():
    # Slowly fade over all HSV colors
    for i in range(0, 255, 2):
        cw.pixels[:] =  hsv_to_rgb(i, 255, 255)
        cw.show()
        time.sleep(0.025)
    cw.pixels[:] = 0, 0, 0
    cw.show()

def test_moving_lines():
    for _ in range(2):
        # Move white line over the horizontal axis, from left to right
        for i in range(20):
            cw.pixels[i:i+1] = 255, 255, 255
            cw.show()
            cw.pixels[i:i+1] = 0, 0, 0
            time.sleep(0.01)

        # Move white line over the horizontal axis, from right to left
        for j in range(20):
            i = 19 - j
            cw.pixels[i:i+1] = 255, 255, 255
            cw.show()
            cw.pixels[i:i+1] = 0, 0, 0
            time.sleep(0.01)
    for _ in range(2):
        # Move white line over the vertical axis, from top to bottom
        for i in range(20):
            cw.pixels[: ,i] = 255, 255, 255
            cw.show()
            cw.pixels[: ,i] = 0, 0, 0
            time.sleep(0.01)   

        # Move white line over the vertical axis, from bottom to top
        for j in range(20):
            i = 19 - j
            cw.pixels[: ,i] = 255, 255, 255
            cw.show()
            cw.pixels[: ,i] = 0, 0, 0
            time.sleep(0.01)  

    cw.pixels[:] = 0, 0, 0
    cw.show()

def test_turning_pixels_on_zigzag():
    # Turning all pixels white row by row in a zigzag
    color = 255, 255, 255
    for _ in range(2): 
        left_to_right = True
        for x in range(0, 20, 2):
            for y in range(0, 20, 2):
                if not left_to_right:
                    y = 18-y
                cw.pixels[x:x+2, y:y+2] = color
                cw.show()
                time.sleep(0.01)
            left_to_right = not left_to_right 
        color = 0, 0, 0

if __name__ == "__main__":
    global cw 
    cw = ContourWall("COM16")

    args = sys.argv[1:]

    tests = {
        "flash_all_colors": test_flash_all_colors,
        "fade_to_white": test_fade_to_white,
        "fade_colors": test_fade_colors,
        "moving_lines": test_moving_lines,
        "turning_pixels_on_zigzag": test_turning_pixels_on_zigzag,
    }

    if len(args) > 0:
        for arg in args:
            if arg == "list":
                print("List of tests:")
                for key in tests.keys():
                    print("  > ", key) 
            elif arg in tests:
                tests[arg]()
            else:
                print(f"[TEST ERROR] No test named: \"{arg}\"")
    else:
        for test in tests.values():
            test()

    print("Pushed frames: ", cw.pushed_frames)
    time.sleep(1)
    cw.pixels[:] = 0, 0, 0
    cw.show()
   