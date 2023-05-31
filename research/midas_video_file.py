import cv2 as cv
import torch
import numpy as np
import time

# model_type = "DPT_Large"
# model_type = "DPT_Hybrid"
model_type = "MiDaS_small"
# model_type = "DPT_SwinV2_T_256"

vid = cv.VideoCapture("sauce/flop_2.mp4")

pTime = 0

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

# out = cv.VideoWriter('outpy.avi',cv.VideoWriter_fourcc('M','J','P','G'), 10, (1920, 1080))

while vid.isOpened():
    _, frame = vid.read()

    input_batch = transform(frame).to(device)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    with torch.no_grad():
        prediction = midas(input_batch)

        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=frame.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    output = prediction.cpu().numpy()

    output = cv.normalize(output, None, 0, 1, norm_type=cv.NORM_MINMAX, dtype=cv.CV_64F)
    output = (output * 255).astype(np.uint8)
    output = cv.applyColorMap(output, cv.COLORMAP_MAGMA)

    # cv.putText(output, "size: " + str(frame.shape[:2]), (70, 110), cv.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3)
    cv.putText(output, "fps: " + str(int(fps)), (70, 50), cv.FONT_HERSHEY_PLAIN, 3, (3, 252, 177), 3)
    
    # out.write(output)

    cv.imshow("output", output)

    if cv.waitKey(1) & 0xFF == ord("q"):
        break

vid.release()
# out.release()
