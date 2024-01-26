from contourwall import ContourWall

import keyboard  # Install: python3.11 -m pip install keyboard

cw = ContourWall("COM16")
loc = [0, 0]

cw.pixels[loc[0], loc[1]] = [0, 0, 255]
cw.show()

def on_arrow_key(event):
    if event.event_type == keyboard.KEY_DOWN:
        cw.pixels[loc[0], loc[1]] = [0, 0, 0]
    
        if event.name == 'up':
            loc[0] -= 1
        elif event.name == 'down':
            loc[0] += 1
        elif event.name == 'left':
            loc[1] -= 1
        elif event.name == 'right':
            loc[1] += 1

        if loc[0] > 19 or loc[0] < 0 or loc[1] > 19 or loc[1] < 0:
            loc[0] = 0
            loc[1] = 0

        cw.pixels[loc[0], loc[1]] = [0, 0, 255]
        cw.show()

keyboard.hook(on_arrow_key)

try:
    print("Press arrow keys. Press 'q' to exit.")
    keyboard.wait('q') 
except KeyboardInterrupt:
    pass
finally:
    keyboard.unhook_all()