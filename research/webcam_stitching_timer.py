import cv2 as cv
import os
import datetime
import imutils as imu
import time

# Initialize camera capture for both cameras (1 and 2 typically represent the first and second cameras)
camera1 = cv.VideoCapture(1, cv.CAP_DSHOW)
camera2 = cv.VideoCapture(2, cv.CAP_DSHOW)

# Check if the cameras are opened successfully
if not camera1.isOpened() or not camera2.isOpened():
    print("Error: Could not open cameras.")
    exit()

# Capture a single frame from each camera
ret1, frame1 = camera1.read()
ret2, frame2 = camera2.read()

# Release camera resources
camera1.release()
camera2.release()

print("[INFO] loading images...")
if ret1 and ret2:
    # Create a directory with the current date and time as the name
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_directory = os.path.join("docs", "stitching", current_time)

    # Create the directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    # Save the captured frames in the directory
    cv.imwrite(os.path.join(save_directory, "cam_l.jpg"), frame1)
    cv.imwrite(os.path.join(save_directory, "cam_r.jpg"), frame2)

    cv.imshow("cam_l", frame1)
    cv.imshow("cam_r", frame2)

    print(f"Images saved in directory: {save_directory}")

    # Perform image stitching
    print("[INFO] stitching images...")
    stitcher = cv.createStitcher() if imu.is_cv3() else cv.Stitcher_create()

    start_time = time.time()
    (status, stitched) = stitcher.stitch([frame1, frame2])
    end_time = time.time()

    if status == cv.Stitcher_OK:
        # Save the stitched image to the "docs/stitching" directory
        stitch_filename = os.path.join(save_directory, f"{current_time}_stitched.jpg")
        cv.imwrite(stitch_filename, stitched)
        print(f"Stitched image saved as {stitch_filename}")

        # Display the stitched image
        cv.imshow("Stitched Image", stitched)

        # Calculate and write the stitching duration to the text file
        stitching_duration = end_time - start_time
        if os.path.exists(save_directory):
            text_filename = os.path.join(save_directory, "testing_data.txt")
            with open(text_filename, "w") as text_file:
                text_file.write(f"Stitching Duration (seconds): {stitching_duration:.4f}\n")
                text_file.write(f"Distance: 25cm\n")
                text_file.write(f"View: forward with camera slanted down\n")
    else:
        # Check if the directory still exists (it might have been renamed in case of a failure)
        if os.path.exists(save_directory):
            text_filename = os.path.join(save_directory, "testing_data.txt")
            with open(text_filename, "w") as text_file:
                text_file.write(f"Distance: 25cm\n")
                text_file.write(f"View: forward with camera slanted down\n")
        print("[INFO] image stitching failed ({})".format(status))

        # Rename the directory to indicate the failure
        os.rename(save_directory, save_directory + " - fail")

    cv.waitKey(0)
    cv.destroyAllWindows()
else:
    print("Error: Failed to capture frames from one or both cameras.")