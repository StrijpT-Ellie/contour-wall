import cv2 as cv
import os
import datetime
import imutils as imu

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
    cv.imwrite(os.path.join(save_directory, "camera1.jpg"), frame1)
    cv.imwrite(os.path.join(save_directory, "camera2.jpg"), frame2)

    cv.imshow("Camera 1", frame1)
    cv.imshow("Camera 2", frame2)

    print(f"Images saved in directory: {save_directory}")

    # Perform image stitching
    print("[INFO] stitching images...")
    stitcher = cv.createStitcher() if imu.is_cv3() else cv.Stitcher_create()

    (status, stitched) = stitcher.stitch([frame1, frame2])
    if status == cv.Stitcher_OK:
        # Save the stitched image to the "docs/stitching" directory
        stitch_filename = os.path.join(save_directory, f"{current_time}_stitched.jpg")
        cv.imwrite(stitch_filename, stitched)
        print(f"Stitched image saved as {stitch_filename}")

        # Display the stitched image
        cv.imshow("Stitched Image", stitched)
    else:
        print("[INFO] image stitching failed ({})".format(status))
        # Rename the directory to indicate the failure
        os.rename(save_directory, save_directory + " - fail")

    text_content = input("Enter text content for the text file: ")

    # Check if the user provided text content
    if text_content:
        # Create and write the text file with user-provided content
        text_filename = os.path.join(save_directory, "testing_data.txt")
        with open(text_filename, "w") as text_file:
            text_file.write(text_content)
            print(f"Text file saved as {text_filename}")
    else:
        print("No text content provided. Text file not created.")

    cv.waitKey(0)
    cv.destroyAllWindows()
else:
    print("Error: Failed to capture frames from one or both cameras.")