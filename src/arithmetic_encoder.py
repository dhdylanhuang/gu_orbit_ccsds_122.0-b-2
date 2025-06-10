#entopy encoding 
#maintain probability models, updating probabilites as data is encoded
#takes  symbols from bitplane encoder and outputs compressed binary stream

#Constants for 32-bit arithmetic
_HIGH = (1 << 32) - 1
_HALF = 1 << 31
_FIRST_QUARTER = 1 << 30
_THIRD_QUARTER = 3 * _FIRST_QUARTER

#Adaptice appraoch to arithmetic coding
def encode_arithmetic(symbols, contexts):
    if not symbols:
        return b''

    #Initialize context models with pseudocounts
    num_ctx = max(contexts) + 1
    zero_counts = [1] * num_ctx
    one_counts = [1] * num_ctx

    low = 0
    high = _HIGH
    underflow = 0
    out_bits = []

    def _output_bit(bit):
        out_bits.append(bit)

    for sym, ctx in zip(symbols, contexts):
        #Compute split point in current interval
        range_size = high - low + 1
        total = zero_counts[ctx] + one_counts[ctx]
        split = low + (range_size * zero_counts[ctx] // total) - 1

        #Narrow interval based on symbol
        if sym == 0:
            high = split
            zero_counts[ctx] += 1
        else:
            low = split + 1
            one_counts[ctx] += 1

        #Renormalize interval and emit bits
        while True:
            if high < _HALF:
                _output_bit(0)
                for _ in range(underflow):
                    _output_bit(1)
                underflow = 0
                low <<= 1
                high = (high << 1) | 1
            elif low >= _HALF:
                _output_bit(1)
                for _ in range(underflow):
                    _output_bit(0)
                underflow = 0
                low = (low - _HALF) << 1
                high = ((high - _HALF) << 1) | 1
            elif low >= _FIRST_QUARTER and high < _THIRD_QUARTER:
                underflow += 1
                low = (low - _FIRST_QUARTER) << 1
                high = ((high - _FIRST_QUARTER) << 1) | 1
            else:
                break

    #Final bits and underflow flush
    underflow += 1
    if low < _FIRST_QUARTER:
        _output_bit(0)
        for _ in range(underflow):
            _output_bit(1)
    else:
        _output_bit(1)
        for _ in range(underflow):
            _output_bit(0)

    #Pack bits into bytes
    bytelist = []
    byte = 0
    for i, b in enumerate(out_bits):
        byte = (byte << 1) | b
        if (i & 7) == 7:
            bytelist.append(byte)
            byte = 0
    rem = len(out_bits) % 8
    if rem:
        byte <<= (8 - rem)
        bytelist.append(byte)

    return bytes(bytelist)