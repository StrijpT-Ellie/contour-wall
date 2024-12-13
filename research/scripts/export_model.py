from ultralytics import YOLO

# Load the model
model = YOLO('yolov8n-seg.pt')

# Export the model
model.export(format='onnx')