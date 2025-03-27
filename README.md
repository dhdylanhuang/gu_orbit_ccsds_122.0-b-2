# CCSDS Compressions

GU Orbit's implementation of CCSDS Image data compression following [CCSDS 122.0-B-2 standard](https://public.ccsds.org/Pubs/122x0b2e1.pdf), focused on lossless compression of bitmap files. 
<br />
The compression ratio achieved is to be compared against a standard implementation of LZW Image Compression. 

## Implementation Flow for Lossless Compression
Our initial implementation in Python, we will be switching to C++ when we are confident in our implementation.
<br />
Bitmap Image Input → DWT (5/3 wavelet) → BPE → Arithmetic Encoding → CCSDS Compliant Bitstream
