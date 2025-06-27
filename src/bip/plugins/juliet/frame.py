import struct
from io import RawIOBase
from typing import Tuple

import pyarrow as pa

header_fmt = "<III"  # https://docs.python.org/3/library/struct.html
header_size = struct.calcsize(header_fmt)
schema = pa.schema([
    ("time_ns", pa.uint64()),
    ("word_count", pa.uint32())
])


def unpack_header(header_bytes: bytes):
    time_msw, time_lsw, word_cnt = struct.unpack(header_fmt, header_bytes)
    return (time_msw << 32) | time_lsw, word_cnt


def read_header(buf: RawIOBase) -> Tuple[int, Tuple[int, int]]:
    header_bytes = buf.read(header_size)
    bytes_read = len(header_bytes)
    if bytes_read == 0:
        return 0, None
    if bytes_read != header_size:
        raise RuntimeError("incomplete read of header")
    return bytes_read, unpack_header(header_bytes)
