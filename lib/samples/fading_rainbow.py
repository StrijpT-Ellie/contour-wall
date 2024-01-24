from contourwall import ContourWall

def scroll(pos):
    color = [0, 0, 0]
    if pos < 85:
        color[2] = (pos / 85) * 255
        color[0] = 255 - color[2]
        color[1] = 0 
    elif pos < 170:
        color[0] = 0;
        color[1] = ((pos - 85) / 85) * 255
        color[2] = 255 - color[1]
    elif pos < 256:
        color[0] = ((pos - 170) / 85) * 255
        color[1] = 255 - color[0]
        color[2] = 1
    return color

cw = ContourWall("COM16")

while True:
    for i in range(255):
        cw.pixels[:] = scroll(i)
        cw.show()
    for i in range(255):
        cw.pixels[:] = scroll(255 - i)
        cw.show()
