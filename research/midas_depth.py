import cv2 as cv
import torch

model_type = "MiDaS_small"
vid = cv.VideoCapture("sauce/flop_2.mp4")

midas = torch.hub.load("intel-isl/MiDaS", model_type)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
midas.to(device)
midas.eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")

if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
    transform = midas_transforms.dpt_transform
else:
    transform = midas_transforms.small_transform
i = 0

while vid.isOpened():
    _, frame = vid.read()

    input_batch = transform(frame).to(device)

    with torch.no_grad():
        prediction = midas(input_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=frame.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    output = prediction.cpu().numpy()
    cv.imshow("output", output)
    if cv.waitKey(1) & 0xFF == ord("q"):
        break
