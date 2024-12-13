import sys
import time
import cv2 as cv
import numpy as np
import mediapipe as mp

WIDTH = 1280
HEIGHT = 720

class HolisticSilhouetteTracker:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            model_complexity=1,
            enable_segmentation=True,
            refine_face_landmarks=True
        )
        
        # Kernels for different morphological operations
        self.clean_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        self.thin_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (2, 2))
        self.leg_kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 7))
        self.side_kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 7))  # Wider kernel for side view
        
    def is_side_view(self, pose_landmarks):
        """Detect if person is in side view based on shoulder positions"""
        if not pose_landmarks:
            return False
            
        # Get shoulder landmarks
        left_shoulder = pose_landmarks.landmark[self.mp_holistic.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = pose_landmarks.landmark[self.mp_holistic.PoseLandmark.RIGHT_SHOULDER]
        
        # Calculate shoulder distance in x-axis
        shoulder_distance = abs(left_shoulder.x - right_shoulder.x)
        
        # If shoulders are close together in x-axis, likely side view
        return shoulder_distance < 0.15  # Threshold for side view detection
        
    def process_mask(self, mask, is_side):
        """Process segmentation mask with view-aware thresholding"""
        h, w = mask.shape
        
        # Split mask into upper and lower parts
        upper_mask = mask[:h//2, :]
        lower_mask = mask[h//2:, :]
        
        if is_side:
            # Side view processing - more lenient thresholds and wider kernels
            upper_binary = (upper_mask > 0.15).astype(np.uint8) * 255
            
            # Process legs with wider kernel for side view
            lower_binary = np.zeros_like(lower_mask, dtype=np.uint8)
            for i in range(lower_mask.shape[0]):
                row_threshold = 0.15 - (i / lower_mask.shape[0]) * 0.05
                lower_binary[i] = (lower_mask[i] > row_threshold) * 255
                
            # Extra processing for side view legs
            lower_binary = cv.morphologyEx(lower_binary, cv.MORPH_CLOSE, self.side_kernel)
        else:
            # Front view processing (same as before)
            upper_binary = (upper_mask > 0.2).astype(np.uint8) * 255
            
            lower_binary = np.zeros_like(lower_mask, dtype=np.uint8)
            for i in range(lower_mask.shape[0]):
                row_threshold = 0.2 - (i / lower_mask.shape[0]) * 0.05
                lower_binary[i] = (lower_mask[i] > row_threshold) * 255
                
            lower_binary = cv.morphologyEx(lower_binary, cv.MORPH_CLOSE, self.leg_kernel)
        
        # Combine masks
        full_mask = np.vstack([upper_binary, lower_binary])
        
        # Final cleanup
        if is_side:
            # Less aggressive thinning for side view
            full_mask = cv.morphologyEx(full_mask, cv.MORPH_CLOSE, self.clean_kernel)
            full_mask = cv.erode(full_mask, self.thin_kernel, iterations=1)
        else:
            full_mask = cv.morphologyEx(full_mask, cv.MORPH_CLOSE, self.clean_kernel)
            full_mask = cv.erode(full_mask, self.thin_kernel, iterations=1)
        
        return full_mask
        
    def create_shaded_silhouette(self, frame, mask):
        # Get brightness from original frame
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        # Normalize brightness to 0.7-1.0 range for subtle shading
        normalized = (gray.astype(float) / 255.0) * 0.3 + 0.7
        
        # Create output image
        shaded = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        # Apply shading only where mask is active
        mask_bool = mask > 127
        for c in range(3):
            shaded[:,:,c] = (normalized * 255 * mask_bool).astype(np.uint8)
            
        return shaded
        
    def process_frame(self, frame):
        if frame is None:
            return None
            
        frame = cv.resize(frame, (WIDTH, HEIGHT))
        frame = cv.flip(frame, 1)
        
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.holistic.process(frame_rgb)
        
        black_bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        if results.segmentation_mask is not None:
            mask = results.segmentation_mask
            mask = cv.resize(mask, (WIDTH, HEIGHT))
            
            # Detect if in side view
            is_side = self.is_side_view(results.pose_landmarks)
            
            # Process mask with view-aware thresholding
            processed_mask = self.process_mask(mask, is_side)
            
            # Create shaded silhouette
            return self.create_shaded_silhouette(frame, processed_mask)
            
        return black_bg
        
    def create_pixelated(self, image, w, h):
        """Create pixelated version with clean edges"""
        # Downscale
        small = cv.resize(image, (w, h), interpolation=cv.INTER_LINEAR)
        
        # Upscale with nearest neighbor to maintain sharp pixels
        pixel = cv.resize(small, (WIDTH, HEIGHT), interpolation=cv.INTER_NEAREST)
        
        return pixel

def create_silhouette(cam_or_vid: str):
    tracker = HolisticSilhouetteTracker()
    previous_frame_time = 0
    cap = cv.VideoCapture(0, cv.CAP_DSHOW) if cam_or_vid == "--webcam" else cv.VideoCapture(cam_or_vid, cv.CAP_DSHOW)
    
    # Pixel art parameters
    w, h = (40, 30)
    
    while True:
        _, frame = cap.read()
        if frame is None:
            break
            
        # Process frame
        shaded_bg = tracker.process_frame(frame)
        
        # Create pixelated version
        pixel_bg = tracker.create_pixelated(shaded_bg.copy(), w, h)
        
        # Add FPS counter only to regular display
        cTime = time.time()
        fps = 1 / (cTime - previous_frame_time)
        previous_frame_time = cTime
        
        cv.putText(
            shaded_bg,
            "fps: " + str(int(fps)),
            (70, 50),
            cv.FONT_HERSHEY_PLAIN,
            3,
            (3, 252, 177),
            3
        )
        
        # Display results
        cv.imshow("Silhouette", shaded_bg)
        cv.imshow("Silhouette pixelated", pixel_bg)
        
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
            
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()
        
    create_silhouette(sys.argv[-1])