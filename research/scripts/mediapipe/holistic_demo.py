import sys
import time
import cv2 as cv
import numpy as np
import mediapipe as mp
from threading import Thread
from collections import deque
from contourwall import ContourWall, hsv_to_rgb

# Constants for LED wall
WIDTH = 60
HEIGHT = 40

class VideoStream:
    def __init__(self, src=0):
        self.cap = cv.VideoCapture(src)
        # Set capture size larger than LED size for better tracking
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv.CAP_PROP_FPS, 30)
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

class HolisticSilhouetteTracker:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,  # Increased to 1 for better multi-person segmentation
            enable_segmentation=True,
            refine_face_landmarks=False
        )
        
        self.kernels = {
            'clean': cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3)),
            'thin': cv.getStructuringElement(cv.MORPH_ELLIPSE, (2, 2)),
            'expand': cv.getStructuringElement(cv.MORPH_ELLIPSE, (4, 4))
        }
        
        # Pre-allocate arrays for LED size
        self.black_bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        self.shaded = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        # Adjust thresholds for multi-person detection
        self.segmentation_threshold = 0.15  # Lower threshold to catch multiple people
        
        self.norm_factor = np.full((HEIGHT, WIDTH), 0.4, dtype=np.float32)
        self.norm_offset = np.full((HEIGHT, WIDTH), 0.6, dtype=np.float32)
        
    def process_mask(self, mask):
        # Simple threshold for initial mask
        binary = (mask > self.segmentation_threshold) * 255
        binary = binary.astype(np.uint8)
        
        # Clean up noise while preserving multiple people
        binary = cv.morphologyEx(binary, cv.MORPH_CLOSE, self.kernels['clean'])
        binary = cv.morphologyEx(binary, cv.MORPH_OPEN, self.kernels['thin'])
        
        # Slightly expand masks to ensure good coverage
        binary = cv.dilate(binary, self.kernels['expand'], iterations=1)
        
        return binary
        
    def create_shaded_silhouette(self, frame, mask):
        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        normalized = np.multiply(gray, self.norm_factor, dtype=np.float32)
        np.add(normalized, self.norm_offset, out=normalized)
        
        mask_bool = mask > 127
        normalized_255 = (normalized * 255).astype(np.uint8)
        
        np.multiply(normalized_255, mask_bool, out=self.shaded[:,:,0])
        self.shaded[:,:,1] = self.shaded[:,:,0]
        self.shaded[:,:,2] = self.shaded[:,:,0]
        
        return self.shaded
        
    def process_frame(self, frame):
        if frame is None:
            return self.black_bg
            
        # Resize input frame to LED dimensions
        frame = cv.resize(frame, (WIDTH, HEIGHT))
        
        # Process frame with MediaPipe
        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self.holistic.process(frame_rgb)
        
        if results.segmentation_mask is not None:
            # Resize mask directly to LED dimensions
            mask = cv.resize(results.segmentation_mask, (WIDTH, HEIGHT))
            processed_mask = self.process_mask(mask)
            return self.create_shaded_silhouette(frame, processed_mask)
            
        return self.black_bg

def create_silhouette(cam_or_vid: str):
    cv.ocl.setUseOpenCL(True)
    
    # Initialize LED wall
    cw = ContourWall()
    cw.new_with_ports("COM11", "COM14", "COM12", "COM13", "COM10", "COM9")
    
    # Initialize video and tracker
    vs = VideoStream(0 if cam_or_vid == "--webcam" else cam_or_vid).start()
    time.sleep(1.0)
    
    tracker = HolisticSilhouetteTracker()
    
    # FPS tracking
    fps_times = deque(maxlen=150)  # 5 seconds at 30fps
    last_fps_print = time.time()
    
    while True:
        frame = vs.read()
        if frame is None:
            break
            
        # Process frame
        frame = cv.flip(frame, 1)
        led_frame = tracker.process_frame(frame)
        
        # Update LED wall
        cw.pixels[:] = led_frame
        cw.show()
        
        # FPS calculation and printing
        current_time = time.time()
        fps_times.append(current_time)
        
        if current_time - last_fps_print >= 5.0:
            if len(fps_times) >= 2:
                avg_fps = len(fps_times) / (fps_times[-1] - fps_times[0])
                print(f"Average FPS over last 5 seconds: {avg_fps:.1f}")
            last_fps_print = current_time
        
        if cv.waitKey(1) & 0xFF == ord("q"):
            break
            
    vs.stop()
    cv.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        exit()
        
    create_silhouette(sys.argv[-1])