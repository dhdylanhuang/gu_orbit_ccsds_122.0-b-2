#2d discrete wavelet transform
#5/3 wavelet for lossless compression 
#perform forward dwt 
#multi-level

# wavelet.py

import numpy as np

#Performs a one-level 1D forward integer on an even-length array using the 5/3 wavelet.
def dwt53_1d(arr):
    N = arr.shape[0]
    assert N % 2 == 0, "Input length must be even for 5/3 DWT."
    half = N // 2
    
    #Allocate arrays for low-pass and high-pass
    low = np.zeros(half, dtype=arr.dtype)
    high = np.zeros(half, dtype=arr.dtype)
    
    #Predict step: compute detail (high-pass) coefficients
    for j in range(half):
        i = 2 * j + 1
        left = arr[i - 1]
        right = arr[i + 1] if (i + 1 < N) else arr[i - 1]
        high[j] = arr[i] - ((left + right) // 2)
    
    #Compute approximation (low-pass) coefficients
    for j in range(half):
        i = 2 * j
        d_left = high[j - 1] if j > 0 else high[j]
        d_right = high[j] if j < (half - 1) else high[j]
        low[j] = arr[i] + ((d_left + d_right + 2) // 4)
    
    #Combine low and high into a single array: [low | high]
    return np.concatenate([low, high])

#Performs a an inverse one-level 1D inverse integer 5/3 DWT on an array of coefficients. 
#This is so first half input is low-pass coefficients and second half is high-pass coefficients.
def idwt53_1d(coeffs):
    N = coeffs.shape[0]
    assert N % 2 == 0, "Input length must be even for inverse 5/3 DWT."
    half = N // 2
    
    low = coeffs[:half]
    high = coeffs[half:]
    
    #Allocate array for the reconstructed signal
    rec = np.zeros(N, dtype=coeffs.dtype)
    
    #Reconstruct even indices
    for j in range(half):
        i = 2 * j
        d_left = high[j - 1] if j > 0 else high[j]
        d_right = high[j] if j < (half - 1) else high[j]
        rec[i] = low[j] - ((d_left + d_right + 2) // 4)
    
    #Inverse predict: reconstruct odd indices
    for j in range(half):
        i = 2 * j + 1
        s_left = rec[i - 1]
        s_right = rec[i + 1] if (i + 1 < N) else rec[i - 1]
        rec[i] = high[j] + ((s_left + s_right) // 2)
    
    return rec

#Performs a multi-level 2D forward integer 5/3 DWT on a 2D image (single channel), returns same shape array of subband coefficients.
def dwt53_2d(img, levels=1):
    out = img.copy()
    H, W = out.shape
    
    for lvl in range(levels):
        rows = H >> lvl
        cols = W >> lvl
        
        #Horizontal transform on each row for this level
        for r in range(rows):
            row = out[r, :cols]
            out[r, :cols] = dwt53_1d(row)
        
        #Vertical transform on each column for this level
        for c in range(cols):
            col = out[:rows, c]
            out[:rows, c] = dwt53_1d(col)
    
    return out

#Performs a multi-level 2D inverse integer 5/3 DWT on a 2D array of coefficients, reconstructs and returns the original 2D image.
def idwt53_2d(coeffs, levels=1):
    out = coeffs.copy()
    H, W = out.shape
    
    for lvl in reversed(range(levels)):
        rows = H >> lvl
        cols = W >> lvl
        
        #Inverse vertical transform on each column for this level
        for c in range(cols):
            col = out[:rows, c]
            out[:rows, c] = idwt53_1d(col)
        
        #Inverse horizontal transform on each row for this level
        for r in range(rows):
            row = out[r, :cols]
            out[r, :cols] = idwt53_1d(row)
    
    return out