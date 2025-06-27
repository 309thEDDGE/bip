""" common value extractions that multiple parsers can implement.
    do consider the payload endianness, and if/when it may be
    converted when using these, little endian is currently assumed """

import numpy as np
import numba

# Current Juliet Implementations


@numba.jit(nopython=True)
def bandwidth(word1, word2):
    raw_data = (np.uint64(word1) << 32) | np.uint64(word2)
    return np.float64(raw_data * (10**-6) * (2**-20))


@numba.jit(nopython=True)
def dwell(word1, word2):
    raw_data = (np.uint64(word1) << 32) | np.uint64(word2)
    # data comes in femtoseconds -9 converts to microseconds
    return np.float64(raw_data * (10**-9))


@numba.jit(nopython=True)
def frequency(word1, word2):
    raw_data = (np.uint64(word1) << 32) | np.uint64(word2)
    return np.float64(raw_data * (10**-9) * (2**-20))


@numba.jit(nopython=True)
def gain(word1):  # needs work, but not implemented in juliet yet
    return word1


@numba.jit(nopython=True)
def offset(word1, word2):
    raw_data = (np.uint64(word1) << 32) | np.uint64(word2)
    return np.float64(raw_data * (10**-6) * (2**-20))


@numba.jit(nopython=True)
def pointing_vector(word):
    el = (word >> 16)
    if el >= 0x8000:  # sign bit present, take 2's complement
        msb = el & 0x8000
        el_out = (0 - msb) + (el - msb)
        el_out = el_out * (2**-7)
    else:
        el_out = el * (2**-7)

    az = (word & 0xFFFF) * (2**-7)
    if az >= 280:
        az = az - 360

    return az, el_out


@numba.jit(nopython=True)
def sample_rate(word1, word2):
    raw_data = (np.uint64(word1) << 32) | np.uint64(word2)
    return np.uint32(raw_data * (10**-6) * (2**-20))


@numba.jit(nopython=True)
def time(tsi, tsf0, tsf1):
    return np.float64(np.uint64(tsi) +
                      ((np.uint64(tsf0) << 32) + np.uint64(tsf1)) * (10**-12))
