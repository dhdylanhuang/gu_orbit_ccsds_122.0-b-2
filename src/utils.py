# src/utils.py

import numpy as np
from PIL import Image

#Reads an RGB BMP image from disk in the range 0-255 and returns a NumPy array of shape (H, W, 3)
def read_rgb_bitmap(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')  # Ensure image is in RGB format
    arr = np.array(img, dtype=np.uint8)
    return arr

#Shifts an unsigned 8-bit array [0,255] to signed integers centered at 0.
def shift_to_signed(arr):
    return arr.astype(np.int16) - 128

#Pads an image array so its height and width are divisible by 'factor'.
def pad_image_to_multiple(arr, factor=2):
    h, w = arr.shape[:2]
    pad_h = (factor - (h % factor)) % factor
    pad_w = (factor - (w % factor)) % factor

    # Define padding specification: ((top, bottom), (left, right), (0, 0) for channels)
    pad_spec = ((0, pad_h), (0, pad_w)) + ((0, 0),) * (arr.ndim - 2)
    return np.pad(arr, pad_spec, mode='edge')
