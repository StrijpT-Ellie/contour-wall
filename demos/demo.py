from contourwall import ContourWall, hsv_to_rgb
import time
import sys

def test_flash_all_colors():
    # Set all pixels to RED
    cw.fill_solid(0, 0, 255)
    cw.show(sleep_ms=500)

    # Set all pixels to RED
    cw.fill_solid(0, 255, 255)
    cw.show(sleep_ms=500)

    # Set all pixels to GREEN
    cw.fill_solid(0, 255, 0)
    cw.show(sleep_ms=500)

    # Set all pixels to GREEN
    cw.fill_solid(255, 255, 0)
    cw.show(sleep_ms=500)

    # Set all pixels to BLUE
    cw.fill_solid(255, 0, 0)
    cw.show(sleep_ms=500)

    # Set all pixels to BLUE
    cw.fill_solid(255, 0, 255)
    cw.show(sleep_ms=500)

    # Set all pixels to WHITE
    cw.fill_solid(255, 255, 255)
    cw.show(sleep_ms=500)

    # Set all pixels to BLACK
    cw.fill_solid(0, 0, 0)
    cw.show(sleep_ms=500)

def test_fade_to_white():
    # Slowly fade to white
    for i in range(0, 255):
        cw.pixels[:] =  i, i, i
        cw.show()
    cw.fill_solid(0, 0, 0)
    cw.show(sleep_ms=10)

def test_fade_colors():
    # Slowly fade over all HSV colors
    for i in range(0, 360):
        cw.pixels[:] =  hsv_to_rgb(i, 100, 100)
        cw.show()
    cw.fill_solid(0, 0, 0)
    cw.show(sleep_ms=10)

def test_moving_lines():
    for _ in range(2):
        # Move white line over the horizontal axis, from left to right
        for i in range(40):
            cw.pixels[i:i+1] = 255, 255, 255
            cw.show()
            cw.pixels[i:i+1] = 0, 0, 0
 
        # Move white line over the horizontal axis, from right to left
        for j in range(40):
            i = 39 - j
            cw.pixels[i:i+1] = 255, 255, 255
            cw.show()
            cw.pixels[i:i+1] = 0, 0, 0
    for _ in range(2):
        # Move white line over the vertical axis, from top to bottom
        for i in range(60):
            cw.pixels[: ,i] = 255, 255, 255
            cw.show()
            cw.pixels[: ,i] = 0, 0, 0   

        # Move white line over the vertical axis, from bottom to top
        for j in range(60):
            i = 59 - j
            cw.pixels[: ,i] = 255, 255, 255
            cw.show()
            cw.pixels[: ,i] = 0, 0, 0

    cw.pixels[:] = 0, 0, 0
    cw.show(sleep_ms=10)

def test_turning_pixels_on_zigzag():
    # Turning all pixels white row by row in a zigzag
    color = 255, 255, 255
    for _ in range(2): 
        left_to_right = True
        for x in range(0, 40, 2):
            for y in range(0, 60, 2):
                if not left_to_right:
                    y = 58-y
                cw.pixels[x:x+2, y:y+2] = color
                cw.show()
            left_to_right = not left_to_right 
        color = 0, 0, 0

if __name__ == "__main__":
    global cw 
    
    cw = ContourWall() 
    cw.new()

    args = sys.argv[1:]

    tests = {
        "flash_all_colors": test_flash_all_colors,
        "fade_to_white": test_fade_to_white,
        "fade_colors": test_fade_colors,
        "moving_lines": test_moving_lines,
        "turning_pixels_on_zigzag": test_turning_pixels_on_zigzag,
    }

    t1 = time.time_ns()

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
   