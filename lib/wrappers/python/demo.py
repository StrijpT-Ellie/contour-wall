from contourwall import ContourWall, hsv_to_rgb
import time
import sys

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
    time.sleep(0.01)

def test_fade_colors():
    # Slowly fade over all HSV colors
    for i in range(0, 255, 2):
        cw.pixels[:] =  hsv_to_rgb(i, 255, 255)
        cw.show()
        time.sleep(0.025)
    cw.pixels[:] = 0, 0, 0
    cw.show()
    time.sleep(0.01)

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
    time.sleep(0.01)

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
    # Example for Windows
    # cw = ContourWall("COM0", baud_rate=2_000_000)
    # Example for Unix
    # cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)
    cw = ContourWall()
    cw.single_new_with_port("COM5")

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
        t1 = time.time_ns()
        for test in tests.values():
            test()
        print("Time elapsed: ", (time.time_ns() - t1 )/1_000_000)

    print("Pushed frames: ", cw.pushed_frames)
    time.sleep(1)
    cw.pixels[:] = 0, 0, 0
    cw.show()
   