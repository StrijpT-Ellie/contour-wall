import os
import cv2 as cv
from ultralytics import YOLO

model = YOLO('yolov8n')

runs_path = 'runs'

video_path = 'sauce/naruto.mp4'
cap = cv.VideoCapture(video_path)

while cap.isOpened():
    succes, frame = cap.read()
    if succes:
        results = model(frame, conf=0.75, imgsz=192)
        annotated_frame = results[0].plot()
        # Display the annotated frame
        cv.imshow("YOLOv8 Inference", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv.destroyAllWindows()


def generate_video():
    video_name = 'test_video.gif'
