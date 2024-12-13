import os
import cv2
import numpy as np
import paddle
from paddleseg.models import PPLiteSeg
from paddleseg.transforms import Compose, Normalize, Resize
from paddleseg.models.backbones import STDC1

class WebcamSegmentation:
    def __init__(self):
        self.model = self.setup_model()
        self.transform = Compose([
            Resize(target_size=(512, 1024)),
            Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])

    def setup_model(self):
        # Create backbone first
        backbone = STDC1(pretrained=None)
        
        # Initialize model with backbone
        model = PPLiteSeg(
            num_classes=2,  # background + person
            backbone=backbone,
            backbone_indices=(2, 3, 4)
        )
        
        # Check if model file exists
        model_path = 'pp_liteseg_stdc1_cityscapes.pdparams'
        if not os.path.exists(model_path):
            print(f"Please download the model file to {model_path}")
            print("You can download it from: https://paddleseg.bj.bcebos.com/dygraph/cityscapes/pp_liteseg_stdc1_cityscapes_1024x512_scale0.5_160k/model.pdparams")
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        params = paddle.load(model_path)
        model.set_dict(params)
        model.eval()
        return model

    def process_frame(self, frame):
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Transform
        transformed = self.transform(frame_rgb)[0]
        input_tensor = paddle.to_tensor(transformed[None, ...])
        
        # Inference
        with paddle.no_grad():
            pred = self.model(input_tensor)[0]
            pred = paddle.argmax(pred, axis=1)
            mask = pred.numpy().astype(np.uint8)[0]
        
        # Resize mask to frame size
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]), 
                         interpolation=cv2.INTER_NEAREST)
        return mask

    def run(self):
        cap = cv2.VideoCapture(0)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                mask = self.process_frame(frame)
                segmented = cv2.bitwise_and(frame, frame, mask=mask)
                
                # Show both original and segmented
                combined = np.hstack((frame, segmented))
                cv2.imshow('Original | Segmented', combined)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    segmentation = WebcamSegmentation()
    segmentation.run()