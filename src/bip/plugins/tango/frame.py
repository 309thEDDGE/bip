from io import (RawIOBase, SEEK_SET)
from typing import Tuple, Optional

import pyarrow as pa


schema = pa.schema([
    ("frame_count", pa.uint32()),
    ("frame_size", pa.uint32()),
    ("start_bytes", pa.uint64()),
    ("frame_index", pa.uint32())
])


def unpack_header(header_bytes: bytes):
    assert len(header_bytes) == 4
    header = int.from_bytes(header_bytes, byteorder="little", signed=False)
    return header >> 20, header & 0xFFFFF


def _check_vrlp(b: bytes):
    if len(b) == 0:
        return None
    elif len(b) != 4:
        raise RuntimeError("incomplete read of VRLP header")
    if b != bytes("PLRV", encoding="ascii"):
        raise RuntimeError("expected VRLP header not found")


def read_header(stream: RawIOBase) -> Tuple[int, Optional[Tuple[int, int]]]:
    buffer = stream.read(4)
    offset = 4

    if len(buffer) == 0:
        return 0, None

    # This while loop makes sure that we are actually
    # at the start of the next packet ignoring garbage
    # that sometimes appears in packets
    while True:
        try:
            _check_vrlp(buffer)
            break
        except RuntimeError:
            pass

        offset += 4
        buffer = stream.read(4)

        if len(buffer) != 4:
            raise RuntimeError("end of file appeared")

    offset += 4
    header_bytes = stream.read(4)
    if len(header_bytes) != 4:
        raise RuntimeError("unable to read header {len(header_bytes + 4)}/8")
    return offset, unpack_header(header_bytes)


# i'm going to assume VRLP will come in on an aligned read, the logic is more
# complex if this isn't true
def first_header(stream: RawIOBase):
    b = stream.read(4)
    if len(b) != 4:
        raise RuntimeError("unable to read stream")

    offset = 0
    while True:
        try:
            _check_vrlp(b)
            break
        except RuntimeError:
            pass

        offset += 4
        b = stream.read(4)

        if len(b) != 4:
            raise RuntimeError("end of file before first packet")

    b = stream.read(4)
    if len(b) != 4:
        raise RuntimeError("incomplete read of first header")
    stream.seek(offset, SEEK_SET)
    return offset
