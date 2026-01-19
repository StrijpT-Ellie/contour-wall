import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
from tkinter.messagebox import showinfo

import time
import os 
import math


WIDTH_FRAME, HEIGHT_FRAME = (1920, 1080)
WIDTH_OUTPUT, HEIGHT_OUTPUT = (40, 30)

def pythagoras_normalized(landmarkA, landmarkB):
    return math.sqrt(
        (landmarkA.x - landmarkB.x) ** 2
        + (landmarkA.y - landmarkB.y) ** 2
    )

def draw_line(landmarkA, landmarkB, frame, wideBoyFactor, hex="FFFFFF"):
    cv2.line(
        frame,
        (int(landmarkA.x), int(landmarkA.y)),
        (int(landmarkB.x), int(landmarkB.y)),
        (tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))),
        int(
            math.ceil(
                pythagoras_normalized(landmarkA, landmarkB)
                / wideBoyFactor
            )
        ),
    )


class PoseMultiDetector:
    def __init__(self, model_path:str,  num_poses=4, min_pose_detection_confidence=0.5, min_pose_presence_confidence=0.5, min_tracking_confidence=0.5):
        self.model_path = model_path
        
        self.num_poses = num_poses
        self.min_pose_detection_confidence = min_pose_detection_confidence
        self.min_pose_presence_confidence = min_pose_presence_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.to_window = None
        self.last_timestamp_ms = 0
        self.base_options = python.BaseOptions(model_asset_path=self.model_path)
        self.options = vision.PoseLandmarkerOptions(
            base_options=self.base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_poses=self.num_poses,
            min_pose_detection_confidence=self.min_pose_detection_confidence,
            min_pose_presence_confidence=self.min_pose_presence_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_segmentation_masks=False,
            result_callback=self.handle_results
        )
        
        self.landmark_arr = []
        
    
    def draw_landmarks_on_image(self, landmarks):
        pose_landmarks_list = landmarks.pose_landmarks #Extracts the list of detected pose landmarks from the detection_result from mediapipe.
        annotated_image = np.zeros((HEIGHT_FRAME, WIDTH_FRAME, 3), dtype = np.uint8)

        person_li = [] #store the landmarks of all detected individuals in the frame
        for pose_landmarks in range(len(pose_landmarks_list)): #Loops through the pose landmarks for each person detected in the frame. Each person has a separate set of landmarks 
            pose_landmarks = pose_landmarks_list[pose_landmarks]
        
            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z) for landmark in pose_landmarks
            ])
            
            for landmark in pose_landmarks:
                    landmark.x, landmark.y = landmark.x * WIDTH_FRAME, landmark.y * HEIGHT_FRAME

            leftEyeInner = pose_landmarks[1]
            leftMouth = pose_landmarks[9]
            leftShoulder = pose_landmarks[11]
            leftElbow = pose_landmarks[13]
            leftWrist = pose_landmarks[15]
            leftIndex = pose_landmarks[19]
            leftHip = pose_landmarks[23]
            leftKnee = pose_landmarks[25]
            leftAnkle = pose_landmarks[27]
            
            rightEyeInner = pose_landmarks[4]
            rightMouth = pose_landmarks[10]
            rightShoulder = pose_landmarks[12]
            rightElbow = pose_landmarks[14]
            rightWrist = pose_landmarks[16]
            rightIndex = pose_landmarks[20]
            rightHip = pose_landmarks[24]
            rightKnee = pose_landmarks[26]
            rightAnkle = pose_landmarks[28]
            
            chestPts = np.array(
                [
                    [rightShoulder.x, rightShoulder.y],
                    [leftShoulder.x, leftShoulder.y],
                    [leftHip.x, leftHip.y],
                    [rightHip.x, rightHip.y],
                ],
                np.int32,
            )

            chestPts = chestPts.reshape((-1, 1, 2))

            neckPts = np.array(
                [
                    [rightShoulder.x, rightShoulder.y],
                    [leftShoulder.x, leftShoulder.y],
                    [leftMouth.x, leftMouth.y],
                    [rightMouth.x, rightMouth.y],
                ],
                np.int32,
            )

            neckPts = neckPts.reshape((-1, 1, 2))
            

            cv2.fillPoly(annotated_image, [chestPts], color=(255, 255, 255))
            cv2.fillPoly(annotated_image, [neckPts], color=(255, 255, 255))

            cv2.ellipse(
                annotated_image,
                (int((rightEyeInner.x + leftEyeInner.x)/2),
                int((rightEyeInner.y + leftEyeInner.y)/2)),
                (int(pythagoras_normalized(rightShoulder, leftShoulder)*0.3),
                int(pythagoras_normalized(rightShoulder, leftShoulder)*0.45)),
                0,
                0,
                360,
                (255, 255, 255),
                -1
                )
            
            cv2.ellipse(
                annotated_image,
                (int(leftWrist.x),
                 int(leftWrist.y)),
                (int(pythagoras_normalized(leftWrist, leftIndex)*0.75),
                int(pythagoras_normalized(leftWrist, leftIndex)*0.75)),
                0,
                0,
                360,
                (255, 255, 255),
                -1
                )
            
            cv2.ellipse(
                annotated_image,
                (int(rightWrist.x),
                 int(rightWrist.y)),
                (int(pythagoras_normalized(rightWrist, rightIndex)*0.75),
                int(pythagoras_normalized(rightWrist, rightIndex)*0.75)),
                0,
                0,
                360,
                (255, 255, 255),
                -1
                )

            draw_line(leftShoulder, rightShoulder, annotated_image, 7)
            draw_line(leftHip, rightHip, annotated_image, 7)
            draw_line(leftShoulder, leftElbow, annotated_image, 3.8)
            draw_line(leftElbow, leftWrist, annotated_image, 5)
            draw_line(leftShoulder, leftHip, annotated_image, 6.5)
            draw_line(leftHip, leftKnee, annotated_image, 3)
            draw_line(leftKnee, leftAnkle, annotated_image, 3.5)
            draw_line(rightShoulder, rightElbow, annotated_image, 3.8)
            draw_line(rightElbow, rightWrist, annotated_image, 5)
            draw_line(rightShoulder, rightHip, annotated_image, 6.5)
            draw_line(rightHip, rightKnee, annotated_image, 3)
            draw_line(rightKnee, rightAnkle, annotated_image, 3.5)
        
            output_pixelated = cv2.resize(annotated_image, (WIDTH_OUTPUT, HEIGHT_OUTPUT), interpolation=cv2.INTER_LINEAR)
            output_pixelated = cv2.resize(output_pixelated, (WIDTH_FRAME, HEIGHT_FRAME), interpolation=cv2.INTER_NEAREST)
            
        self.landmark_arr.append(np.array(person_li))
    
        return annotated_image

    # Function gets called, when landmarker.detect_async() is done.
    def handle_results(self, landmarks: vision.PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        if timestamp_ms < self.last_timestamp_ms:
            return
        self.last_timestamp_ms = timestamp_ms
        self.to_window = cv2.cvtColor(
            self.draw_landmarks_on_image(landmarks), cv2.COLOR_RGB2BGR)

    def detect_pose_landmarks(self):
        previous_frame_time = 0
        with vision.PoseLandmarker.create_from_options(self.options) as landmarker:
            cap = cv2.VideoCapture(0) #The videocapture input can be different depending on your device
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    print("Image capture failed.")
                    break
                
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                timestamp_ms = int(time.time() * 1000)

                # When function is done, it call self.handle_results
                landmarker.detect_async(mp_image, timestamp_ms)

                if self.to_window is not None:
                    # Resize and flip the frame to fit the target dimensions
                    frame = cv2.resize(self.to_window, (WIDTH_FRAME, HEIGHT_FRAME))
                    frame = cv2.flip(frame, 1)
                    cTime = time.time()
                    fps = 1 / (cTime - previous_frame_time) if previous_frame_time > 0 else 0
                    previous_frame_time = cTime
                    
                    output_pixelated = cv2.resize(frame, (WIDTH_OUTPUT, HEIGHT_OUTPUT), interpolation=cv2.INTER_LINEAR)
                    output_pixelated = cv2.resize(output_pixelated, (WIDTH_FRAME, HEIGHT_FRAME), interpolation=cv2.INTER_NEAREST)
                    cv2.putText(
                        frame, "fps: " + str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3
                    )
                    cv2.imshow("MediaPipe Pose Landmark", frame)
                    cv2.imshow("MediaPipe Pose Landmark Pixelated", output_pixelated)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            
        array = np.transpose(np.array(self.landmark_arr), (1,0,2,3))
        return array

    def run(self):
        self.array = self.detect_pose_landmarks()
        self.array = self.add_center(landmark = self.array) # (2, 1066, 35, 3) => (person, frame, landmark, xyz)
        return self.array

if __name__ == '__main__':
    start_time = time.time() 
    
    # Model_path src : https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#models 
    # Make sure you have the model downloaded in the models folder
    detector = PoseMultiDetector(model_path="models/pose_landmarker_lite.task")
    array = detector.run()
    
    end_time = time.time() 
    elapsed_time = end_time - start_time  

