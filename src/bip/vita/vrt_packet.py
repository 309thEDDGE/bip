import numpy as np


class VRTPacketHeader:
    def __init__(self, value):
        self.value = int(value)

    def __int__(self):
        return self.value

    @property
    def packet_type(self) -> int:
        return self.value >> 28

    @property
    def class_id(self) -> bool:
        return bool(self.value & (1 << 27))

    @property
    def indicators(self) -> int:
        return (self.value & (0x7 << 24)) >> 24

    @property
    def tsi(self) -> int:
        return (self.value & (0x3 << 22)) >> 22

    @property
    def tsf(self) -> int:
        return (self.value & (0x3 << 20)) >> 20

    @property
    def packet_count(self) -> int:
        return (self.value & (0xF << 16)) >> 16

    @property
    def packet_size(self) -> int:
        return (self.value & 0xFFFF)


class VRTPacket:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.words = np.frombuffer(self.payload, dtype=np.uint32)

    @property
    def packet_header(self):
        return VRTPacketHeader(self.words[0])

    @property
    def stream_identifier(self):
        return self.words[1]

    @property
    def class_identifier(self):
        return self.words[2:4]

    @property
    def integer_timestamp(self):
        return self.words[4]

    @property
    def fractional_timestamp(self):
        return self.words[5:7]
