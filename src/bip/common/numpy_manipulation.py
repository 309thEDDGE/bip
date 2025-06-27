import numpy as np
import numba


def rolling_window(array, window):
    shape = array.shape[:-1] + (array.shape[-1] - window + 1, window)
    strides = array.strides + (array.strides[-1],)
    return np.lib.stride_tricks.as_strided(array, shape=shape, strides=strides)


def find_subarray_indexes_numpy(array, subarray):
    """
    Finds all starting indexes where `array` equals `subarray`.
    """
    temp = rolling_window(array, len(subarray))
    result = np.nonzero(np.all(temp == subarray, axis=1))
    return result[0] if result else None


@numba.jit(nopython=True)
def find_subarray_indexes_numba(array, subarray):
    """
    Finds all starting indexes where `array` equals `subarray`.
    """

    # There is probably a more efficient way to do this, but if you profile
    # bip itself you'll see that this isn't a significant bottleneck.
    array_idx = 0
    match_length = 0
    sub_len = len(subarray)
    array_len = len(array)
    indexes = []

    while array_idx < array_len:
        match_length = 0
        while (
            # Haven't matched the entire subarray yet.
            match_length < sub_len and
            # Haven't reached the end of the array yet.
            array_idx + match_length < array_len and
            # Array still matches subarray
            array[array_idx + match_length] == subarray[match_length]
        ):
            match_length += 1

        if match_length == sub_len:
            indexes.append(array_idx)

        array_idx += 1

    if len(indexes) > 0:
        return np.array(indexes)

    return None


find_subarray_indexes = find_subarray_indexes_numba
