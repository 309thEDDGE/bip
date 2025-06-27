from . vrt_packet import VRTPacket
from . class_identifier import ClassIdentifier


class ContextIndicators:
    def __init__(self, header):
        self.value = header

    @property
    def timestamp_mode(self) -> bool:
        return bool(self.value & (1 << 24))

    @property
    def not_vita_49_0(self) -> bool:
        return bool(self.value & (1 << 25))


class ContextPacket(VRTPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

    @property
    def context_indicators(self) -> ContextIndicators:
        return ContextIndicators(self.words[0])

    @property
    def stream_id(self) -> int:
        return self.words[1]

    @property
    def class_id(self) -> ClassIdentifier:
        return ClassIdentifier(self.words[2:4])
