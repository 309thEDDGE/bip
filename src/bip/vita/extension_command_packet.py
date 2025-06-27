from . vrt_packet import VRTPacket


class ExtensionCommandPacket(VRTPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

    @property
    def stream_id(self) -> int:
        return self.words[1]
