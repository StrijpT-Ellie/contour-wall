import cv2 as cv
import argparse

parser = argparse.ArgumentParser(description="Capture images from cameras and perform stitching.")
parser.add_argument("--num_cameras", type=int, default=2, help="Number of cameras connected.")
args = parser.parse_args()

cameras = [cv.VideoCapture(idx, cv.CAP_DSHOW) for idx in range(args.num_cameras)]

# Check if the cameras are opened successfully
for idx, camera in enumerate(cameras):
    if not camera.isOpened():
        print(f"[INFO]: Could not open camera {idx}.")
        cameras[idx] = None

while True:
    for idx, camera in enumerate(cameras):
        if camera is not None:
            # Read a frame from the camera
            ret, frame = camera.read()

            if ret:
                # Display the frame from the camera
                cv.imshow(f"camera_{idx}", frame)

    # Exit the loop when the 'q' key is pressed
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera resources and close OpenCV windows
for camera in cameras:
    if camera is not None:
        camera.release()
cv.destroyAllWindows()
