import os
import glob
import cv2
import numpy as np

image_dir = os.path.join(os.path.abspath('.'), "GEOTIFF")
fname = glob.glob(os.path.join(image_dir, '*.tif'))

print(image_dir)

img: np.ndarray = cv2.imread(filename=fname[0], flags=cv2.IMREAD_UNCHANGED)

x, y, w, h = 4100, 7600, 512, 512
ROI = img[y:y+h, x:x+w]

normalized_img: np.ndarray = cv2.normalize(ROI, dst=None, alpha=256.0, beta=0.0, norm_type=cv2.NORM_MINMAX).astype(np.uint8)
cv2.imshow("image", normalized_img)
cv2.waitKey(0)


