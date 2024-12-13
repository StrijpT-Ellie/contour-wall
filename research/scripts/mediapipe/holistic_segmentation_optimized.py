import sys
import time
import cv2 as cv
import numpy as np
import mediapipe as mp
from threading import Thread

WIDTH = 1280
HEIGHT = 720

class VideoStream:
    def __init__(self, src=0):
        self.cap = cv.VideoCapture(src)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        self.cap.set(cv.CAP_PROP_FPS, 30)  # Request 30fps from camera
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        
    def start(self):
        Thread(target=self.update, args=(), daemon=True).start()
        return self
        
    def update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.cap.read()
            
    def read(self):
        return self.frame
        
    def stop(self):
        self.stopped = True

class MultiPersonHolisticTracker:
    def __init__(self):
        # Initialize MediaPipe solutions
        self.mp_pose = mp.solutions.pose
        self.mp_holistic = mp.solutions.holistic
        
        # Initialize Pose for multi-person detection
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )
        
        # Initialize Holistic for high-quality segmentation
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0,
            enable_segmentation=True,
            refine_face_landmarks=False
        )
        
        # Pre-compute all kernels
        self.kernels = {
            'clean': cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3)),
            'thin': cv.getStructuringElement(cv.MORPH_ELLIPSE, (2, 2)),
            'leg': cv.getStructuringElement(cv.MORPH_RECT, (3, 9)),
            'side': cv.getStructuringElement(cv.MORPH_RECT, (5, 9))
        }
        
        # Cache landmark indices
        self.LEFT_SHOULDER = self.mp_pose.PoseLandmark.LEFT_SHOULDER.value
        self.RIGHT_SHOULDER = self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value
        
        # Pre-allocate reusable arrays
        self.black_bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.shaded = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.combined_mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
        
        # Pre-compute gradient maps for efficient processing
        h_half = HEIGHT // 2
        self.row_indices = np.arange(h_half)
        base_gradient = np.square(self.row_indices / h_half) * 0.08
        self.gradient = base_gradient[:, np.newaxis]
        
        # Pre-compute threshold maps
        self.side_thresholds = 0.15 - self.gradient
        self.front_thresholds = 0.2 - self.gradient
        
        # Pre-compute normalization factors
        self.norm_factor = np.full((HEIGHT, WIDTH), 0.4, dtype=np.float32)
        self.norm_offset = np.full((HEIGHT, WIDTH), 0.6, dtype=np.float32)
        
    def is_side_view(self, landmarks):
        if not landmarks:
            return False
        left = landmarks[self.LEFT_SHOULDER].x
        right = landmarks[self.RIGHT_SHOULDER].x
        return abs(left - right) < 0.15
        
    def process_mask(self, mask, is_side):
        h = mask.shape[0]
        mid = h // 2
        
        # Process upper and lower parts efficiently
        upper_threshold = 0.15 if is_side else 0.2
        upper_binary = (mask[:mid] > upper_threshold) * 255
        
        # Apply pre-computed thresholds
        thresholds = self.side_thresholds if is_side else self.front_thresholds
        lower_binary = (mask[mid:] > thresholds) * 255
        
        # Combine masks using pre-allocated array
        full_mask = np.vstack([upper_binary, lower_binary]).astype(np.uint8)
        
        # Apply optimal morphological operations
        kernel = self.kernels['side'] if is_side else self.kernels['leg']
        full_mask = cv.morphologyEx(full_mask, cv.MORPH_CLOSE, kernel)
        
        if not is_side:
            full_mask = cv.erode(full_mask, self.kernels['thin'], iterations=1)
        
        return full_mask
        
    def create_shaded_silhouette(self, frame, mask):
        # Efficient grayscale conversion and normalization
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # Apply pre-computed normalization factors
        normalized = np.multiply(gray, self.norm_factor, dtype=np.float32)
        np.add(normalized, self.norm_offset, out=normalized)
        
        # Create final output efficiently
        mask_bool = mask > 127
        normalized_255 = (normalized * 255).astype(np.uint8)
        
        # Use pre-allocated array for output
        np.multiply(normalized_255, mask_bool, out=self.shaded[:,:,0])
        self.shaded[:,:,1] = self.shaded[:,:,0]
        self.shaded[:,:,2] = self.shaded[:,:,0]
        
        return self.shaded
        
    def process_frame(self, frame):
        if frame is None:
            return self.black_bg
            
        # Convert frame to RGB for MediaPipe
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        
        # Get holistic segmentation first
        holistic_results = self.holistic.process(frame_rgb)
        if holistic_results.segmentation_mask is None:
            return self.black_bg
            
        # Get pose detection for multiple people
        pose_results = self.pose.process(frame_rgb)
        
        # Get the high-quality holistic segmentation mask
        holistic_mask = cv.resize(holistic_results.segmentation_mask, (WIDTH, HEIGHT))
        
        # Start with the holistic processed mask
        is_side = self.is_side_view(holistic_results.pose_landmarks.landmark if holistic_results.pose_landmarks else None)
        processed_mask = self.process_mask(holistic_mask, is_side)
        self.combined_mask = processed_mask.copy()
        
        # If additional people are detected by pose, process their regions
        if pose_results.pose_landmarks:
            is_side_pose = self.is_side_view(pose_results.pose_landmarks.landmark)
            pose_processed = self.process_mask(holistic_mask, is_side_pose)
            self.combined_mask = cv.bitwise_or(self.combined_mask, pose_processed)
        
        return self.create_shaded_silhouette(frame, self.combined_mask)
        
    @staticmethod
    def create_pixelated(image, w, h):
        return cv.resize(
            cv.resize(image, (w, h), interpolation=cv.INTER_LINEAR),
            (WIDTH, HEIGHT),
            interpolation=cv.INTER_NEAREST
        )
    
def create_silhouette(cam_or_vid: str):
    # Enable OpenCL if available
    cv.ocl.setUseOpenCL(True)
    
    # Initialize video stream with threading
    vs = VideoStream(0 if cam_or_vid == "--webcam" else cam_or_vid).start()
    time.sleep(1.0)  # Warm up camera
    
    tracker = MultiPersonHolisticTracker()
    previous_frame_time = 0
    w, h = 60, 40
    
    # Pre-compute text parameters
    font = cv.FONT_HERSHEY_PLAIN
    font_scale = 1.5
    font_color = (3, 252, 177)
    font_thickness = 2
    font_position = (35, 25)
    
    while True:
        frame = vs.read()
        if frame is None:
            break
            
        # Process frame
        frame = cv.resize(cv.flip(frame, 1), (WIDTH, HEIGHT))
        shaded_bg = tracker.process_frame(frame)
        pixel_bg = tracker.create_pixelated(shaded_bg, w, h)
        
        # Calculate FPS
        cTime = time.time()
        fps = int(1 / (cTime - previous_frame_time))
        previous_frame_time = cTime
        
        # Add FPS counter
        cv.putText(
            shaded_bg,
            f"fps: {fps}",
            font_position,
            font,
            font_scale,
            font_color,
            font_thickness
        )
        
        # Display results
        cv.imshow("Silhouette", shaded_bg)
        cv.imshow("Silhouette pixelated", pixel_bg)
        
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
            
    vs.stop()
    cv.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()
        
    create_silhouette(sys.argv[-1])