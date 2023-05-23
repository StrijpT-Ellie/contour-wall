import cv2 as cv
from ultralytics import YOLO
import time

person_type = 0

model = YOLO('yolov8n-seg.pt')

cap = cv.VideoCapture(0)

previous_time_frame = 0

while cap.isOpened():
    succes, frame = cap.read()

    if succes:
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - previous_time_frame)
        previous_time_frame = new_frame_time
        fps = int(fps)
        fps = 'fps: ' + str(fps)
        results = model(frame, classes=person_type, imgsz=160)
        annotated_frame = results[0].plot()
        cv.putText(annotated_frame, fps, (7, 70), cv.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv.LINE_AA)
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
