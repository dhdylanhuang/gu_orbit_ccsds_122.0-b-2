#!/usr/bin/env python3

import argparse
import numpy as np
from src.ccsds122_encoder import compress as ccsds_compress
from src.ccsds122_decoder import decompress as ccsds_decompress


def main():
    parser = argparse.ArgumentParser(
        description="CCSDS 122.0-B-2 Image Compressor/Decompressor"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--compress', nargs=2, metavar=('INPUT_BMP', 'OUTPUT_CCSDS'),
        help='Compress an RGB BMP to CCSDS 122.0-B-2 format'
    )
    group.add_argument(
        '--decompress', nargs=2, metavar=('INPUT_CCSDS', 'OUTPUT_BMP'),
        help='Decompress a CCSDS 122.0-B-2 file to BMP'
    )
    parser.add_argument(
        '--levels', type=int, default=1,
        help='Number of DWT levels to use (default: 1)'
    )
    args = parser.parse_args()

    if args.compress:
        inp, out = args.compress
        print(f"Compressing '{inp}' → '{out}' with {args.levels} DWT level(s) ...")
        ccsds_compress(inp, out, levels=args.levels)
        print(f"Compression complete. Output: {out}")

    elif args.decompress:
        inp, out = args.decompress
        print(f"Decompressing '{inp}' → '{out}' ...")
        ccsds_decompress(inp, out)
        print(f"Decompression complete. Output: {out}")


if __name__ == '__main__':
    main()
