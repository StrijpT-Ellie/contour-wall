import cv2 as cv
import argparse
import tkinter as tk
import mediapipe as mp

# Initialize mediapipe pose and draw objects
mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose

# Argument parsing
parser = argparse.ArgumentParser(description="Pose estimation and image processing script.")
parser.add_argument("--video", action="store_true")
parser.add_argument("--webcam", action="store_true")
args = parser.parse_args()

if args.webcam:
    feed_video = cv.VideoCapture(0, cv.CAP_DSHOW)
else:
    feed_video = cv.VideoCapture("../../sauce/final_location/wouter_400_150_50_cropped/wouter_400_100_50_increments.mp4")

# Get first frame of the video to determine its resolution and then the aspect ratio
_, first_frame = feed_video.read()

native_video_height, native_video_width, _ = first_frame.shape

native_video_aspect_ratio = native_video_width / native_video_height

print(f"[INFO] Current video resolution: {native_video_width} x {native_video_height}")
print(f"[INFO] Current video aspect ratio: {native_video_aspect_ratio}")

# Current display resolution information gathering
dummy_window = tk.Tk()
dummy_window.withdraw()

screen_width = dummy_window.winfo_screenwidth()
screen_height = dummy_window.winfo_screenheight()

dummy_window.destroy()

print(f"[INFO] Current screen resolution: {screen_width} x {screen_height}")

# Determine the minimum scaling factor to ensure video maintains its aspect ratio but fills the screen height-wise
width_scale = screen_width / native_video_width
height_scale = screen_height / native_video_height
scale_factor = min(width_scale, height_scale)

print(f"[INFO] Maximum resolution of scaled video: {int(native_video_width*scale_factor)} x {int(native_video_height*scale_factor)}")

# Initialize pose object
with mpPose.Pose(model_complexity=0) as pose:

    

    # Reading video
    while feed_video.isOpened():
        # Get native image directly from the feed_video, be it a webcam feed or a video
        _, feed_image = feed_video.read()

        # If nothing is returned, break out of the loop
        if not _:
            break

        # Upscale image to fill the entire screen on which it is being displayed
        native_resolution_image = cv.resize(feed_image, None, fx=scale_factor, fy=scale_factor)

        # Convert feed_image to RGB for Mediapipe
        rbg_image = cv.cvtColor(native_resolution_image, cv.COLOR_BGR2RGB)

        # Show rgb_image
        cv.imshow("rbg_image", rbg_image)
        cv.namedWindow('rbg_image', cv.WINDOW_NORMAL)
        
        # Wait for "q" to be pressed if the user wants to end the show of the video earlier
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
        
feed_video.release()
cv.destroyAllWindows()