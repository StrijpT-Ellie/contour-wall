import cv2 as cv
import torch
import numpy as np

filename = 'sauce/workspace.jpg'
img = cv.imread(filename)

model_type = "DPT_Large"
# model_type = "DPT_Hybrid"
# model_type = "MiDaS_small"

midas = torch.hub.load("intel-isl/MiDaS", model_type)

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
midas.to(device)
midas.eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")

if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
    transform = midas_transforms.dpt_transform
else:
    transform = midas_transforms.small_transform

input_batch = transform(img).to(device)

with torch.no_grad():
    prediction = midas(input_batch)

    prediction = torch.nn.functional.interpolate(
        prediction.unsqueeze(1),
        size=img.shape[:2],
        mode="bicubic",
        align_corners=False,
    ).squeeze()

output = prediction.cpu().numpy()

output = cv.normalize(output, None, 0, 1, norm_type=cv.NORM_MINMAX, dtype=cv.CV_64F)
output = (output * 255).astype(np.uint8)
output = cv.applyColorMap(output, cv.COLORMAP_VIRIDIS)

scale_percent = 35 # percent of original size
width = int(output.shape[1] * scale_percent / 100)
height = int(output.shape[0] * scale_percent / 100)
dim = (width, height)

output = cv.resize(output, dim, interpolation = cv.INTER_LINEAR)
img = cv.resize(img, dim, interpolation = cv.INTER_LINEAR)

cv.imshow('output', output)
cv.imwrite('docs/large_viridis_trilinear.jpg', output)
cv.imwrite('docs/workspace.jpg', img)

cv.waitKey(0)
cv.destroyAllWindows()