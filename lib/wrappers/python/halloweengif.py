#!/usr/bin/env python3
import os
import sys
sys.path.append(r"C:\Users\Melissa\Desktop\ellie\contour-wall\lib\wrappers\python")
import cv2
import numpy as np
import time
from ultralytics import YOLO
from threading import Thread
import queue
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional, Union, Set
from contourwall import ContourWall


@dataclass
class Config:
    """Configuration parameters for video processing"""
    width: int = 320  # Camera capture width
    height: int = 240  # Camera capture height
    fps: int = 15
    process_every_n_frames: int = 2
    position_threshold: int = 50
    tracking_history_length: int = 30
    consecutive_frames_threshold: int = 5
    min_brightness: float = 0.4
    brightness_range: float = 0.6
    pixelate_width: int = 60  # Match LED wall width
    pixelate_height: int = 40  # Match LED wall height

class VideoStream:
    """Threaded video capture from webcam or video file"""
    
    def __init__(self, src: Union[int, str], config: Config):
        self.config = config
        self.stream = cv2.VideoCapture(src)
        if isinstance(src, int):  # Webcam setup
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
            self.stream.set(cv2.CAP_PROP_FPS, config.fps)
            
        if not self.stream.isOpened():
            raise RuntimeError("Could not open video stream")
            
        self.stopped = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.frame_count = 0

    def start(self) -> 'VideoStream':
        Thread(target=self._update, args=(), daemon=True).start()
        return self

    def _update(self) -> None:
        while not self.stopped:
            if not self.frame_queue.full():
                ret, frame = self.stream.read()
                if not ret:
                    self.stop()
                    return
                
                self.frame_count += 1
                frame = cv2.resize(frame, (self.config.width, self.config.height))
                frame = cv2.flip(frame, 1)  # Mirror webcam
                should_process = (self.frame_count % self.config.process_every_n_frames == 0)
                self.frame_queue.put((frame, should_process))
            else:
                time.sleep(0.001)  # Prevent CPU thrashing

    def read(self) -> Tuple[Optional[np.ndarray], bool]:
        try:
            return self.frame_queue.get(timeout=1.0)
        except queue.Empty:
            return None, False

    def stop(self) -> None:
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()

class PersonTracker:
    """Tracks multiple people across frames using IOU and distance matching"""
    
    def __init__(self, config: Config):
        self.config = config
        self.tracking_history: Dict[int, List[Tuple[int, int, int, int]]] = {}
        self.next_person_id = 0
        
    def calculate_iou(self, box1: Tuple[int, int, int, int], 
                     box2: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union between two bounding boxes"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[0] + box1[2], box2[0] + box2[2])
        y2 = min(box1[1] + box1[3], box2[1] + box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = box1[2] * box1[3]
        area2 = box2[2] * box2[3]
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def get_person_id(self, bbox: Tuple[int, int, int, int]) -> int:
        """Match current detection with existing person tracks"""
        x, y, w, h = bbox
        center = (x + w // 2, y + h // 2)
        
        # Try IOU matching first
        best_match = None
        best_iou = 0.3  # IOU threshold
        
        for person_id, history in self.tracking_history.items():
            if not history:
                continue
            iou = self.calculate_iou(bbox, history[-1])
            if iou > best_iou:
                best_iou = iou
                best_match = person_id

        # Fall back to distance-based matching
        if best_match is None:
            min_distance = float('inf')
            for person_id, history in self.tracking_history.items():
                if not history:
                    continue
                last_x, last_y, last_w, last_h = history[-1]
                last_center = (last_x + last_w // 2, last_y + last_h // 2)
                distance = np.hypot(center[0] - last_center[0], 
                                  center[1] - last_center[1])
                
                if distance < min_distance and distance < self.config.position_threshold:
                    min_distance = distance
                    best_match = person_id

        # Create new track if no match found
        if best_match is None:
            best_match = self.next_person_id
            self.next_person_id += 1
            self.tracking_history[best_match] = []

        # Update history
        self.tracking_history[best_match].append(bbox)
        if len(self.tracking_history[best_match]) > self.config.tracking_history_length:
            self.tracking_history[best_match].pop(0)

        return best_match

    def cleanup_old_tracks(self, active_ids: Set[int]) -> None:
        """Remove tracks that haven't been seen recently"""
        for person_id in list(self.tracking_history.keys()):
            if person_id not in active_ids:
                if len(self.tracking_history[person_id]) > self.config.tracking_history_length:
                    del self.tracking_history[person_id]

class MultiPersonSegmentation:
    """Segments and tracks multiple people in video frames"""
    
    def __init__(self, config: Config):
        self.config = config
        print("Initializing YOLO model...")
        self.model = YOLO('yolov8n-seg.pt')
        self.model.to('cpu')
        print("Model loaded on CPU")
        
        self.tracker = PersonTracker(config)
        self.shaded = np.zeros((config.height, config.width, 3), dtype=np.uint8)
        
        # Initialize color palette
        self.colors = np.array([
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255)
        ], dtype=np.uint8)
        self.person_colors: Dict[int, Tuple[int, int, int]] = {}

    def get_track_color(self, person_id: int) -> Tuple[int, int, int]:
        """Get or create a consistent color for a person ID"""
        if person_id not in self.person_colors:
            color = self.colors[person_id % len(self.colors)]
            self.person_colors[person_id] = tuple(map(int, color))
        return self.person_colors[person_id]

    def clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """Clean up segmentation mask using morphological operations"""
        if mask.shape[:2] != (self.config.height, self.config.width):
            mask = cv2.resize(mask, (self.config.width, self.config.height))
        
        mask = (mask * 255).astype(np.uint8)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask

    def process_frame(self, frame: np.ndarray, should_process: bool) -> np.ndarray:
        """Process a video frame to create silhouette visualization"""
        if not should_process:
            return self.shaded
            
        try:
            results = self.model.predict(
                source=frame,
                conf=0.5,
                classes=0,  # person class
                verbose=False,
                stream=True,
                device='cpu'
            )
            
            result = next(results, None)
            active_ids: Set[int] = set()
            
            # Clear the shaded buffer
            self.shaded = np.zeros((self.config.height, self.config.width, 3), dtype=np.uint8)
            
            if result and result.masks is not None and len(result.masks) > 0:
                # Create brightness map from grayscale image
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                gray = self.config.min_brightness + (gray * self.config.brightness_range)
                gray = np.clip(gray, self.config.min_brightness, 1.0) * 255
                
                for seg in result.masks.data:
                    mask = self.clean_mask(seg.cpu().numpy())
                    if not mask.any():
                        continue
                    
                    contours, _ = cv2.findContours(
                        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if not contours:
                        continue
                        
                    x, y, w, h = cv2.boundingRect(contours[0])
                    person_id = self.tracker.get_person_id((x, y, w, h))
                    active_ids.add(person_id)
                    
                    color = self.get_track_color(person_id)
                    mask_bool = mask > 127
                    
                    # Apply colored mask with brightness variation
                    for c in range(3):
                        self.shaded[:, :, c] = np.where(
                            mask_bool,
                            gray * (color[c] / 255),
                            self.shaded[:, :, c]
                        )
                
                self.tracker.cleanup_old_tracks(active_ids)
            
            return self.shaded
            
        except Exception as e:
            print(f"Error during inference: {str(e)}")
            return self.shaded

def create_silhouette(cam_or_vid: str) -> None:
    """Main function to run person silhouette detection"""
    config = Config()
    print(f"Opening video source: {cam_or_vid}")
    
    # Initialize ContourWall
    print("Initializing LED wall...")
    try:
        os.add_dll_directory(r"C:\Users\Melissa\Desktop\ellie\contour-wall\lib\wrappers\python")
        cw = ContourWall()
        cw.new_with_ports(
            "COM9",
            "COM10",
            "COM11",
            "COM12",
            "COM7",
            "COM8"
        )
        led_wall_enabled = True
        print("LED wall initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize LED wall: {e}")
        print("Continuing without LED wall output")
        led_wall_enabled = False

    try:
        source = 0 if cam_or_vid == "--webcam" else cam_or_vid
        video_stream = VideoStream(source, config).start()
        time.sleep(2.0)  # Allow camera to warm up
    except Exception as e:
        print(f"Error opening video source: {e}")
        return
    
    print("Initializing segmenter...")
    segmenter = MultiPersonSegmentation(config)
    
    # Initialize FPS tracking
    fps_bg = np.zeros((30, 100, 3), dtype=np.uint8)
    frame_times: List[float] = []
    
    print("Starting main loop...")
    try:
        while True:
            result = video_stream.read()
            if result is None:
                print("Failed to read frame")
                break
                
            frame, should_process = result
            
            # Update FPS calculation
            current_time = time.time()
            frame_times = [t for t in frame_times if current_time - t < 1.0]
            frame_times.append(current_time)
            fps = len(frame_times)

            # Process frame and create visualizations
            shaded_bg = segmenter.process_frame(frame, should_process)
            
            # Create LED wall version with correct dimensions
            led_output = cv2.resize(shaded_bg, (config.pixelate_width, config.pixelate_height), 
                                  interpolation=cv2.INTER_NEAREST)
            
            # Create preview version
            preview_pixel = cv2.resize(led_output, (config.width, config.height), 
                                     interpolation=cv2.INTER_NEAREST)
            

            # Send to LED wall if available

            # Send to LED wall if available
            if led_wall_enabled:
                try:
                    # First create the pixelated version at 60x40
                    led_output = cv2.resize(shaded_bg, (60, 40), interpolation=cv2.INTER_NEAREST)
                    
                    # Each pixel will now be a single color in our 60x40 grid
                    colors = np.zeros((40, 60, 3), dtype=np.uint8)
                    
                    # Extract color values for each cell
                    for y in range(40):
                        for x in range(60):
                            colors[y, x] = led_output[y, x]
                    
                    # Send to LED wall
                    cw.pixels[:] = colors
                    cw.show()
                    
                except Exception as e:
                    print(f"Error updating LED wall: {e}")
                    led_wall_enabled = False
            
            # Add FPS display
            display_bg = shaded_bg.copy()
            display_bg[0:30, 0:100] = fps_bg
            cv2.putText(display_bg, f"FPS: {int(fps)}", (10, 20),
                       cv2.FONT_HERSHEY_PLAIN, 1, (3, 252, 177), 1)
            
            # Show preview windows
            cv2.imshow("Silhouette", display_bg)
            cv2.imshow("Silhouette pixelated", preview_pixel)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        print("Cleaning up...")
        video_stream.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide either '--webcam', or a filename of a video")
        sys.exit(1)
    create_silhouette(sys.argv[-1])