import numpy as np
from src.utils import read_rgb_bitmap, shift_to_signed, pad_image_to_multiple
from src.wavelet import dwt53_2d, idwt53_2d

#CLI, passes arguments to the encoder and decoder
#ccsds122_encoder.py to comress 
#ccsds122_decoder.py to decompress


# 1. Read the RGB BMP:
rgb_array = read_rgb_bitmap('data/sample_640×426.bmp')

# 2. Shift to signed integers (for lossless wavelet):
signed_array = shift_to_signed(rgb_array)

# 3. Pad so both dimensions are even (factor=2 for one‐level DWT):
padded_array = pad_image_to_multiple(signed_array, factor=2)

# 4. If RGB, split into three separate 2D planes:
r_plane = padded_array[:, :, 0]
g_plane = padded_array[:, :, 1]
b_plane = padded_array[:, :, 2]

print("Padded R plane shape:", r_plane.shape)
print("Padded G plane shape:", g_plane.shape)
print("Padded B plane shape:", b_plane.shape)

r_plane_coeffs = dwt53_2d(r_plane, levels=1)
g_plane_coeffs = dwt53_2d(g_plane, levels=1)
b_plane_coeffs = dwt53_2d(b_plane, levels=1)

reconstructed_r = idwt53_2d(r_plane_coeffs, levels=1)
reconstructed_g = idwt53_2d(g_plane_coeffs, levels=1)
reconstructed_b = idwt53_2d(b_plane_coeffs, levels=1)

assert np.array_equal(r_plane, reconstructed_r)
assert np.array_equal(g_plane, reconstructed_g)
assert np.array_equal(b_plane, reconstructed_b)
