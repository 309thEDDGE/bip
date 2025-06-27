from . extension_command_packet import ExtensionCommandPacket
from . signal_data_packet import SignalDataPacket
from . context_packet import ContextPacket
from . vrt_packet import VRTPacketHeader
from . vrt_packet import VRTPacket


def vrt_header(payload: bytes):
    return VRTPacketHeader(int.from_bytes(payload[0:4], byteorder='little'))


def vrt_packet(payload: bytes):
    return VRTPacket(payload)


__all__ = [
    "ExtensionCommandPacket",
    "SignalDataPacket",
    "ContextPacket"
]
