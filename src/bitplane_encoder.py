#represents coefficients as binary numbers in bitplanes
#transmits most sig bit-planes first then least sig bit-planes

import numpy as np

#Extracts subbands from a 2D coefficient array in scanning order.
def get_subbands(coeff, levels=1):
    H, W = coeff.shape
    subbands = []
    #LL at highest level
    rows_k = H // (2 ** levels)
    cols_k = W // (2 ** levels)
    subbands.append(coeff[:rows_k, :cols_k])

    #detail bands for each level from k down to 1
    for lvl in range(levels, 0, -1):
        rows = H // (2 ** lvl)
        cols = W // (2 ** lvl)
        #LH: low rows, high cols
        subbands.append(coeff[rows:2*rows, :cols])
        #HL: high rows, low cols
        subbands.append(coeff[:rows, cols:2*cols])
        #HH: high rows, high cols
        subbands.append(coeff[rows:2*rows, cols:2*cols])

    return subbands

#Encodes a list of 2D DWT coefficient arrays into bit-plane symbols and contexts.
def encode_bitplanes(coeffs_list, levels=1):
    #Gather all subbands in scan order
    subbands = []
    for coeff in coeffs_list:
        subbands.extend(get_subbands(coeff, levels))

    #Flatten coefficients into 1D array
    if subbands:
        coeff_array = np.concatenate([sb.flatten() for sb in subbands])
    else:
        coeff_array = np.array([], dtype=int)

    #Sign-magnitude conversion
    signs = coeff_array < 0
    mags = np.abs(coeff_array)

    #Determine max bit-plane
    if mags.size > 0 and mags.max() > 0:
        max_mag = mags.max()
        nbp = int(np.floor(np.log2(max_mag)))
    else:
        nbp = 0

    #Initialize significance map
    significance = np.zeros_like(mags, dtype=bool)

    symbols = []
    contexts = []

    #Context indices
    SIGNIFICANCE_CTX = 0
    SIGN_CTX = 1
    REFINEMENT_CTX = 2

    #Bit-plane scanning from MSB to LSB
    for b in range(nbp, -1, -1):
        #Significance & refinement
        for i, mag in enumerate(mags):
            bit = (mag >> b) & 1
            if not significance[i]:
                symbols.append(int(bit))
                contexts.append(SIGNIFICANCE_CTX)
                if bit:
                    significance[i] = True
                    symbols.append(int(signs[i]))
                    contexts.append(SIGN_CTX)
            else:
                #refinement bit for already significant
                symbols.append(int(bit))
                contexts.append(REFINEMENT_CTX)

    return symbols, contexts