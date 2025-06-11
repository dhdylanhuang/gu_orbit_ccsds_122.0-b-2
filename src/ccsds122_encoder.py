#integrates modules
#takes raw bitmap image and outputs compressed binary stream

import struct
import binascii
from src.utils import read_rgb_bitmap, shift_to_signed, pad_image_to_multiple
from src.wavelet import dwt53_2d
from src.bitplane_encoder import encode_bitplanes
from src.arithmetic_encoder import encode_arithmetic

# Maximum CCSDS packet payload size (bytes)
_MAX_PACKET_SIZE = 64 * 1024  # 64 KB

#Build global header
#Fields: 
#magic: 4s 'C122', orig_height: H (uint16), orig_width: W (uint16),
#components: C (uint8), levels: L (uint8), pad_height: Hp (uint16),
#pad_width: Wp (uint16), wavelet_type: 1 byte (1 = integer 5/3), CRC32: 4 bytes
def build_global_header(orig_shape, padded_shape, levels):
    H, W, C = orig_shape
    Hp, Wp, _ = padded_shape
    # placeholder CRC (0); will patch after bitstream known
    header = struct.pack('>4sHHBBHHB', b'C122', H, W, C, levels, Hp, Wp, 1)
    return header

#Build per-packet header
def build_packet_header(seq, length):
    return struct.pack('>HI', seq, length)

def compress(input_path: str, output_path: str, levels=1):
    # 1. Preprocessing
    rgb = read_rgb_bitmap(input_path)
    signed = shift_to_signed(rgb)
    padded = pad_image_to_multiple(signed, factor=2**levels)

    # 2. DWT per channel
    coeffs = []
    for c in range(rgb.shape[2]):
        plane = padded[:, :, c]
        coeffs.append(dwt53_2d(plane, levels=levels))

    # 3. Bit-plane encode
    symbols, contexts = encode_bitplanes(coeffs, levels=levels)

    # 4. Arithmetic encode
    bitstream = encode_arithmetic(symbols, contexts)

    # 5. Build global header (CRC placeholder)
    global_header = build_global_header(rgb.shape, padded.shape, levels)
    # compute CRC of bitstream
    crc = binascii.crc32(bitstream) & 0xffffffff
    # append CRC to header
    global_header += struct.pack('>I', crc)

    # 6. Write output: header + packetized payload
    with open(output_path, 'wb') as f:
        # write header
        f.write(global_header)
        # write packets
        seq = 0
        for i in range(0, len(bitstream), _MAX_PACKET_SIZE):
            chunk = bitstream[i:i + _MAX_PACKET_SIZE]
            pkt_hdr = build_packet_header(seq, len(chunk))
            f.write(pkt_hdr)
            f.write(chunk)
            seq += 1
