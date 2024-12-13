# Standard library imports
import os
import sys
# Add path to custom library
sys.path.append(r"C:\Users\Melissa\Desktop\ellie\contour-wall\lib\wrappers\python")

# Third-party imports
import cv2
import numpy as np
import time
from ultralytics import YOLO
from threading import Thread
import queue
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional, Union, Set
# Custom library import
from contourwall import ContourWall

@dataclass
class Config:
    """Configuration parameters for video processing and silhouette detection
    
    Attributes:
        width (int): Width of processed video frames
        height (int): Height of processed video frames
        fps (int): Target frames per second for video capture
        process_every_n_frames (int): Process only every nth frame for performance
        position_threshold (int): Threshold for position change detection
        tracking_history_length (int): Number of frames to keep in tracking history
        consecutive_frames_threshold (int): Required consecutive frames for detection
        pixelate_width (int): Width of pixelated output
        pixelate_height (int): Height of pixelated output
        min_contour_area (int): Minimum area for valid contours
        mask_dilation_size (int): Size of dilation kernel for mask processing
        mask_erosion_size (int): Size of erosion kernel for mask processing
        blur_kernel_size (int): Size of blur kernel for mask smoothing
        confidence_threshold (float): Minimum confidence for YOLO detections
    """
    width: int = 180
    height: int = 120
    fps: int = 30
    process_every_n_frames: int = 3
    position_threshold: int = 50
    tracking_history_length: int = 30
    consecutive_frames_threshold: int = 5
    pixelate_width: int = 30
    pixelate_height: int = 20
    min_contour_area: int = 300  
    mask_dilation_size: int = 2 
    mask_erosion_size: int = 1   
    blur_kernel_size: int = 3  
    confidence_threshold: float = 0.35 

class VideoStream:
    """Threaded video capture class for efficient frame reading
    
    Implements a producer-consumer pattern using a queue to ensure smooth
    video capture without blocking the main processing loop.
    """
    
    def __init__(self, src: Union[int, str], config: Config):
        """Initialize video capture from webcam or video file
        
        Args:
            src: Video source (0 for webcam, or path to video file)
            config: Configuration parameters
        """
        self.config = config
        self.stream = cv2.VideoCapture(src)
        if isinstance(src, int):  # Configure webcam settings
            self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)
            self.stream.set(cv2.CAP_PROP_FPS, config.fps)
            self.stream.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
        if not self.stream.isOpened():
            raise RuntimeError("Could not open video stream")
            
        self.stopped = False
        self.frame_queue = queue.Queue(maxsize=1)  # Only keep latest frame
        self.frame_count = 0

    def start(self) -> 'VideoStream':
        """Start the video capture thread"""
        Thread(target=self._update, args=(), daemon=True).start()
        return self

    def _update(self) -> None:
        """Continuously read frames from the video source
        
        Processes frames by resizing and applying basic pre-processing,
        then adds them to the queue for consumption by the main thread.
        """
        while not self.stopped:
            if not self.frame_queue.full():
                ret, frame = self.stream.read()
                if not ret:
                    self.stop()
                    return
                
                self.frame_count += 1
                # Resize and pre-process frame
                frame = cv2.resize(frame, (self.config.width, self.config.height))
                frame = cv2.flip(frame, 1)  # Mirror for natural interaction
                frame = cv2.medianBlur(frame, 3)  # Remove noise
                
                # Flag frames for processing based on configured interval
                should_process = (self.frame_count % self.config.process_every_n_frames == 0)
                self.frame_queue.put((frame, should_process))
            else:
                time.sleep(0.001)  # Prevent tight loop

    def read(self) -> Tuple[Optional[np.ndarray], bool]:
        """Read the next frame from the queue
        
        Returns:
            Tuple of (frame, should_process flag)
        """
        try:
            return self.frame_queue.get(timeout=1.0)
        except queue.Empty:
            return None, False

    def stop(self) -> None:
        """Stop video capture and release resources"""
        self.stopped = True
        if self.stream.isOpened():
            self.stream.release()

class MultiPersonSegmentation:
    """Handles person detection and segmentation using YOLO
    
    Uses YOLOv8 with segmentation to detect people and create silhouettes,
    applying various post-processing steps to clean up the output.
    """
    
    def __init__(self, config: Config):
        """Initialize YOLO model and processing parameters"""
        self.config = config
        print("Initializing YOLO model...")
        self.model = YOLO('yolov8n-seg.pt')  # Load nano segmentation model
        self.model.to('cpu')  # Ensure CPU inference
        print("Model loaded on CPU")
        self.shaded = np.zeros((config.height, config.width, 3), dtype=np.uint8)
        
        # Create kernels for morphological operations
        self.erosion_kernel = np.ones((config.mask_erosion_size, 
                                     config.mask_erosion_size), np.uint8)
        self.dilation_kernel = np.ones((config.mask_dilation_size, 
                                      config.mask_dilation_size), np.uint8)

    def clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """Apply post-processing to improve segmentation mask quality
        
        Args:
            mask: Raw segmentation mask from YOLO
            
        Returns:
            Cleaned and processed binary mask
        """
        # Ensure correct dimensions
        if mask.shape[:2] != (self.config.height, self.config.width):
            mask = cv2.resize(mask, (self.config.width, self.config.height))
        
        # Convert to binary mask and apply initial smoothing
        mask = (mask * 255).astype(np.uint8)
        mask = cv2.GaussianBlur(mask, (self.config.blur_kernel_size, 
                                      self.config.blur_kernel_size), 0)
        mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Fill holes using flood fill
        mask_flood = mask.copy()
        h, w = mask.shape[:2]
        fill_mask = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(mask_flood, fill_mask, (0, 0), 255)
        mask_flood_inv = cv2.bitwise_not(mask_flood)
        mask = cv2.bitwise_or(mask, mask_flood_inv)
        
        # Final cleanup with morphological operations
        mask = cv2.erode(mask, self.erosion_kernel, iterations=1)
        mask = cv2.dilate(mask, self.dilation_kernel, iterations=1)
        
        return mask

    def process_frame(self, frame: np.ndarray, should_process: bool) -> np.ndarray:
        """Process a video frame to detect and segment people
        
        Args:
            frame: Input video frame
            should_process: Flag indicating if full processing is needed
            
        Returns:
            Frame with drawn silhouettes
        """
        if not should_process:
            return self.shaded
            
        try:
            # Run YOLO inference
            results = self.model.predict(
                source=frame,
                conf=self.config.confidence_threshold,
                classes=0,  # Only detect person class
                verbose=False,
                stream=True,
                device='cpu',
                iou=0.45
            )
            
            result = next(results, None)
            self.shaded.fill(0)  # Clear previous frame
            
            if result and result.masks is not None and len(result.masks) > 0:
                # Create combined mask for all detected people
                combined_mask = np.zeros((self.config.height, self.config.width), dtype=np.uint8)
                
                for seg in result.masks.data:
                    mask = self.clean_mask(seg.cpu().numpy())
                    combined_mask = cv2.bitwise_or(combined_mask, mask)
                
                # Find and filter contours
                contours, _ = cv2.findContours(
                    combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filter and smooth contours
                valid_contours = []
                for cnt in contours:
                    if cv2.contourArea(cnt) > self.config.min_contour_area:
                        # Smooth contour
                        epsilon = 0.001 * cv2.arcLength(cnt, True)
                        smoothed_cnt = cv2.approxPolyDP(cnt, epsilon, True)
                        valid_contours.append(smoothed_cnt)
                
                # Draw filled contours for silhouettes
                if valid_contours:
                    cv2.drawContours(self.shaded, valid_contours, -1, (255, 255, 255), -1)
            
            return self.shaded
            
        except Exception as e:
            print(f"Error during inference: {str(e)}")
            return self.shaded

def create_silhouette(cam_or_vid: str) -> None:
    """Main function to run real-time person silhouette detection
    
    Sets up video capture, LED wall connection, and runs the main processing loop
    that detects people and displays their silhouettes.
    
    Args:
        cam_or_vid: Either "--webcam" for webcam input or path to video file
    """
    config = Config()
    print(f"Opening video source: {cam_or_vid}")
    
    # Initialize LED wall connection
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

    # Set up video capture
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
            # Read and process frame
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

            # Process frame and create silhouettes
            shaded_bg = segmenter.process_frame(frame, should_process)
            
            # Create LED wall output
            led_output = cv2.resize(shaded_bg, (60, 40), interpolation=cv2.INTER_LINEAR)
            led_output_rgb = cv2.cvtColor(led_output, cv2.COLOR_BGR2RGB)
            
            # Create preview at original size
            preview_pixel = cv2.resize(led_output, (config.width, config.height), 
                                     interpolation=cv2.INTER_NEAREST)

            # Update LED wall if available
            if led_wall_enabled:
                try:
                    cw.pixels[:] = led_output_rgb
                    cw.show()
                except Exception as e:
                    print(f"Error updating LED wall: {e}")
                    led_wall_enabled = False
            
            # Add FPS display to preview
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