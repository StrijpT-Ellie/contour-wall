# Common Errors & Solutions

This page lists common problems you may encounter when working with the Contour Wall, along with their solutions.

---

### The tiles are in a wrong order
Something probablu went wrong with replacing the string "YOUR COM PORT" in the demo.py script with COM port that the Contourwall is connnected to.
Example: cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)

Behind the Contour Wall you will find a **USB hub**. Each USB connection corresponds to one tile. When using `new_with_ports`, the order of the ports must match the physical order of the tiles.

Before:
```python
    cw = ContourWall("/dev/ttyUSB0", baud_rate=2_000_000)
```
After:
```python
cw.new_with_ports(
    "/dev/cu.usbmodem564D0089331",
    "/dev/cu.usbmodem564D0089332",
    ...
)
```

You need to find out which usb is which usbmodem and hardcode them in the correct order.

### Cannot find Webcam input
If your demo uses a webcam and the camera feed does not appear, the camera index is likely incorrect.
Different devices assign webcams to different indices and the correct input can't be found. Make sure the correct camera index is selected, try out changing the input: `cap = cv2.VideoCapture(0)` to `cap = cv2.VideoCapture(1)`.

