import cv2 as cv
import os
import datetime
import imutils as imu
import time
import argparse

# Initialize the argument parser
parser = argparse.ArgumentParser(description="Capture images from cameras and perform stitching.")
parser.add_argument("--num_cameras", type=int, default=2, help="Number of cameras connected.")
parser.add_argument("--builtin_camera", action="store_false", help="Integrated camera present.")
args = parser.parse_args()

camera_indices = list(range(args.num_cameras))
if not args.builtin_camera:
    camera_indices = [idx for idx in camera_indices if idx not in [0, 1]] # Remove integrated cameras

# Initialize camera captures for indexed cameras
cameras = [cv.VideoCapture(idx, cv.CAP_DSHOW) for idx in camera_indices]

# Check if indexed cameras were opened correctly
if not all(camera.isOpened() for camera in cameras):
    print("[INFO] Could not open cameras.")
    exit()

# Capture a single frame from each camera
frames = [camera.read()[1] for camera in cameras]

# Release camera resources
for camera in cameras:
    camera.release()

print("[INFO] Loading images...")
if all(frame is not None for frame in frames):
    # Create a directory with the current date and time as the name
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_directory = os.path.join("docs", "stitching", current_time)

    # Create the directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    # Save the captured frames in the directory
    for i, frame in enumerate(frames):
        cv.imwrite(os.path.join(save_directory, f"camera_{i+1}.jpg"), frame)

    cv.imshow("camera_left", frames[0])
    cv.imshow("camera_right", frames[1])

    print(f"[INFO] Images saved in directory: {save_directory}")

    # Perform image stitching
    print("[INFO] Stitching images...")
    stitcher = cv.createStitcher() if imu.is_cv3() else cv.Stitcher_create()

    start_time = time.time()
    (status, stitched) = stitcher.stitch(frames)
    end_time = time.time()

    if status == cv.Stitcher_OK:
        # Save the stitched image to the "docs/stitching" directory
        stitch_filename = os.path.join(save_directory, f"{current_time}_stitched.jpg")
        cv.imwrite(stitch_filename, stitched)
        print(f"[INFO] Stitched image saved as {stitch_filename}")
 
        # Display the stitched image
        cv.imshow("Stitched image", stitched)

        # Calculate and write the stitching duration to the text file
        stitching_duration = end_time - start_time
        if os.path.exists(save_directory):
            text_filename = os.path.join(save_directory, "testing_data.txt")
            with open(text_filename, "w") as text_file:
                text_file.write(f"Stitching Duration (seconds): {stitching_duration:.4f}\n")
                text_file.write(f"Distance: 100cm\n")
                text_file.write(f"View: forward, auto-exposure off\n")
    else:
        # Check if the directory still exists (it might have been renamed in case of a failure)
        if os.path.exists(save_directory):
            text_filename = os.path.join(save_directory, "testing_data.txt")
            with open(text_filename, "w") as text_file:
                text_file.write(f"Distance: 100cm\n")
                text_file.write(f"View: forward, auto-exposure off\n")
        print("[INFO] Image stitching failed ({})".format(status))

        # Rename the directory to indicate the failure
        os.rename(save_directory, save_directory + " - fail")

    cv.waitKey(0)
    cv.destroyAllWindows()
else:
    print("[INFO] Failed to capture frames from one or both cameras.")
