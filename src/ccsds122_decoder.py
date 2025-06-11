# src/ccsds122_decoder.py

import struct
import binascii
import numpy as np
from PIL import Image
from src.wavelet import idwt53_2d

# Constants matching encoder
_MAX_PACKET_SIZE = 64 * 1024
_HIGH = (1 << 32) - 1
_HALF = 1 << 31
_FIRST_QUARTER = 1 << 30
_THIRD_QUARTER = 3 * _FIRST_QUARTER


def make_arithmetic_decoder(bitstream_bytes, num_contexts=3):
    """
    Create a next-bit decoder function for adaptive binary arithmetic coding.

    Returns a function decode_bit(ctx) that yields one decoded bit for context ctx.
    """
    # Initialize counts
    zero_counts = [1] * num_contexts
    one_counts = [1] * num_contexts
    # Convert bytes to bit list
    bits = [(b >> i) & 1 for b in bitstream_bytes for i in range(7, -1, -1)]
    ptr = 0

    def read_bit():
        nonlocal ptr
        if ptr < len(bits):
            bit = bits[ptr]
            ptr += 1
            return bit
        return 0

    # Initialize interval and code value
    low, high = 0, _HIGH
    code = 0
    for _ in range(32):
        code = (code << 1) | read_bit()

    def decode_bit(ctx):
        nonlocal low, high, code
        # Compute split
        total = zero_counts[ctx] + one_counts[ctx]
        range_size = high - low + 1
        split = low + (range_size * zero_counts[ctx] // total) - 1
        # Determine symbol
        if code <= split:
            sym = 0
            high = split
            zero_counts[ctx] += 1
        else:
            sym = 1
            low = split + 1
            one_counts[ctx] += 1
        # Renormalize
        while True:
            if high < _HALF:
                pass
            elif low >= _HALF:
                code -= _HALF
                low -= _HALF
                high -= _HALF
            elif low >= _FIRST_QUARTER and high < _THIRD_QUARTER:
                code -= _FIRST_QUARTER
                low -= _FIRST_QUARTER
                high -= _FIRST_QUARTER
            else:
                break
            low = low << 1
            high = (high << 1) | 1
            code = (code << 1) | read_bit()
        return sym

    return decode_bit


def decompress(input_path: str, output_path: str):
    """
    Decompress a CCSDS 122.0-B-2 file into a BMP.
    """
    # 1. Read global header and payload
    with open(input_path, 'rb') as f:
        header_fmt = '>4sHHBBHHB'
        header_size = struct.calcsize(header_fmt)
        header = f.read(header_size)
        magic, H, W, C, levels, Hp, Wp, wavelet_type = struct.unpack(header_fmt, header)
        if magic != b'C122':
            raise ValueError(f"Not a CCSDS 122 bitstream: magic={magic}")
        crc_stored = struct.unpack('>I', f.read(4))[0]
        # Read packets
        bitstream = bytearray()
        while True:
            pkt_hdr = f.read(6)
            if not pkt_hdr:
                break
            seq, length = struct.unpack('>HI', pkt_hdr)
            bitstream.extend(f.read(length))

    # 2. Verify CRC
    crc_calc = binascii.crc32(bitstream) & 0xFFFFFFFF
    if crc_calc != crc_stored:
        raise ValueError(f"CRC mismatch: stored={crc_stored:#08x}, calc={crc_calc:#08x}")

    # 3. Prepare arithmetic decoder
    decode_next = make_arithmetic_decoder(bytes(bitstream), num_contexts=3)

    # 4. Build subband scan-order and shapes
    region_slices = []
    shapes = []
    # LL_k
    rows_k = Hp // (2 ** levels)
    cols_k = Wp // (2 ** levels)
    region_slices.append((slice(0, rows_k), slice(0, cols_k)))
    shapes.append((rows_k, cols_k))
    # Detail bands
    for lvl in range(levels, 0, -1):
        rows = Hp // (2 ** lvl)
        cols = Wp // (2 ** lvl)
        # LH
        region_slices.append((slice(rows, 2*rows), slice(0, cols)))
        shapes.append((rows, cols))
        # HL
        region_slices.append((slice(0, rows), slice(cols, 2*cols)))
        shapes.append((rows, cols))
        # HH
        region_slices.append((slice(rows, 2*rows), slice(cols, 2*cols)))
        shapes.append((rows, cols))
    subbands_per_channel = 1 + 3 * levels

    # 5. Total coefficients and bit-planes
    total_coeffs = C * sum(h * w for (h, w) in shapes)
    nbp = 8 + levels  # safe upper bound

    # 6. Allocate arrays
    mags = np.zeros(total_coeffs, dtype=int)
    signs = np.zeros(total_coeffs, dtype=bool)
    significant = np.zeros(total_coeffs, dtype=bool)

    # 7. Decode bit-planes
    idx = 0
    for b in range(nbp - 1, -1, -1):
        for k in range(total_coeffs):
            if not significant[k]:
                flag = decode_next(0)  # significance context
                if flag:
                    significant[k] = True
                    sign_bit = decode_next(1)  # sign context
                    signs[k] = bool(sign_bit)
                mags[k] |= (flag << b)
            else:
                bit_ref = decode_next(2)  # refinement context
                mags[k] |= (bit_ref << b)

    # 8. Reconstruct coefficient arrays per channel
    coeffs_list = []
    ptr = 0
    for ch in range(C):
        coeff_mat = np.zeros((Hp, Wp), dtype=int)
        for sb in range(subbands_per_channel):
            h, w = shapes[sb]
            size = h * w
            block = mags[ptr:ptr + size].reshape((h, w))
            ptr += size
            rs, cs = region_slices[sb]
            coeff_mat[rs, cs] = block
        coeffs_list.append(coeff_mat)

    # 9. Inverse DWT per channel
    planes = [idwt53_2d(coeffs, levels=levels) for coeffs in coeffs_list]

    # 10. Rebuild image, unpad, shift back
    img_padded = np.stack(planes, axis=2)
    img_unpadded = img_padded[:H, :W, :]
    img_uint8 = (img_unpadded + 128).astype(np.uint8)

    # 11. Save BMP
    mode = 'RGB' if C == 3 else 'L'
    Image.fromarray(img_uint8, mode=mode).save(output_path)