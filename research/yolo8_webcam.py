import cv2 as cv
import numpy as np
from ultralytics import YOLO
import time

person_type = 0

model = YOLO('yolov8n-seg.pt')

cap = cv.VideoCapture(0)

previous_time_frame = 0

while cap.isOpened():
    success, frame = cap.read()
    if success:
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - previous_time_frame)
        previous_time_frame = new_frame_time
        fps = int(fps)
        fps = 'fps: ' + str(fps)
        results = model(frame, classes=person_type, imgsz=192)

        # segmentation_mask = results[0].masks.data.numpy().transpose(1, 2, 0)
        # inverted_mask = 1 - segmentation_mask
        #
        # coloured_mask = np.expand_dims(segmentation_mask, 0).repeat(3, axis=0)
        # coloured_mask = np.moveaxis(coloured_mask, 0, -1)
        #
        # inverted_coloured_mask = np.expand_dims(inverted_mask, 0).repeat(3, axis=0)
        # inverted_coloured_mask = np.moveaxis(inverted_coloured_mask, 0, -1)
        #
        # masked = np.ma.MaskedArray(frame, mask=coloured_mask, fill_value=(255, 255, 255))
        # inverted_masked = np.ma.MaskedArray(frame, mask=inverted_coloured_mask, fill_value=(0, 0, 0))
        #
        # image_overlay = masked.filled()
        # inverted_overlay = inverted_masked.filled()
        annotated_frame = results[0].plot()

        # combined_image = (inverted_overlay << image_overlay) - (image_overlay * image_overlay)
        cv.putText(annotated_frame, fps, (7,70), cv.FONT_HERSHEY_SIMPLEX, 3, (100,255,0), 3, cv.LINE_AA)
        cv.imshow("Overlay test", annotated_frame)
        # Break the loop if 'q' is pressed
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv.destroyAllWindows()
