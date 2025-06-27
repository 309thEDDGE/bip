from pathlib import Path

import pyarrow as pa
import numpy as np

from bip.vita import ExtensionCommandPacket as VitaExtensionCommandPacket
from bip.common import bit_manipulation
from typing import Optional


_schema = [
    ("packet_id", pa.uint32()),

    # header
    ("packet_size", pa.uint16()),
    ("packet_count", pa.uint16()),
    ("tsfd", pa.uint8()),
    ("tsid", pa.uint8()),
    ("indicators", pa.uint8()),
    ("packet_type", pa.uint8()),
    ("stream_id", pa.uint32()),
    ("classId0", pa.uint32()),
    ("classId1", pa.uint32()),
    ("tsi", pa.uint32()),
    ("tsf0", pa.uint32()),
    ("tsf1", pa.uint32()),
    ("time", pa.float64(), "gps"),
    ("cam", pa.uint32()),
    ("message_id", pa.uint32()),
    ("cif0", pa.uint32()),
    ("cif2", pa.uint32()),
    ("cif4", pa.uint32()),
    ("cited_SID", pa.uint32()),
    ("reject_reason", pa.uint32()),
    ("data_addr_index", pa.uint32()),
    ("frame_index", pa.uint32()),
    ("packet_index", pa.uint32()),
]


def _schema_elt(e: tuple) -> dict:
    if len(e) > 2 and e[2] is not None:
        unit = {"unit": str(e[2])}
    else:
        unit = {}

    return {
        "name": e[0],
        "type": str(e[1]),
    } | unit


schema = [_schema_elt(e) for e in _schema]


# TODO: cancellation and acknowledgement flags aren't handled or stored
class _ExtensionCommandPacket(VitaExtensionCommandPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        self.time = bit_manipulation.time(tsi, tsf0, tsf1)
        self.classId0, self.classId1 = self.class_identifier
        self.cam = self.words[7]
        self.message_id = self.words[8]
        self.cif0 = self.words[9]
        self.cif2 = self.words[10]
        self.cif4 = self.words[11]
        self.cited_sid = self.words[12]
        self.reject_reason = self.words[13]
        self.data_addr_index = self.words[14]


class AckR_Packet:
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: Optional[dict] = None,
                 batch_size: int = 1000,
                 **kwargs):
        if recorder_opts is None:
            recorder_opts = {}

        self.options = kwargs
        self.recorder = Recorder(
            output_path,
            schema=pa.schema([(e[0], e[1]) for e in _schema]),
            options=recorder_opts,
            batch_size=batch_size)

        self.packet_id = 0

    def __add_record(self,
                     packet: _ExtensionCommandPacket,
                     *,
                     frame_index: int,
                     packet_index: int
                     ):
        assert isinstance(packet, _ExtensionCommandPacket)
        header = packet.packet_header

        self.recorder.add_record({
            "packet_id": np.uint32(self.packet_id),
            "packet_size": np.uint16(header.packet_size),
            "packet_count": np.uint16(header.packet_count),
            "tsfd": np.uint8(header.tsf),
            "tsid": np.uint8(header.tsi),
            "indicators": np.uint8(header.indicators),
            "packet_type": np.uint8(header.packet_type),
            "stream_id": np.uint32(packet.stream_id),
            "classId0": np.uint32(packet.classId0),
            "classId1": np.uint32(packet.classId1),
            "tsi": np.uint32(packet.integer_timestamp),
            "tsf0": np.uint32(packet.fractional_timestamp[0]),
            "tsf1": np.uint32(packet.fractional_timestamp[1]),
            "time": np.float64(packet.time),
            "cam": np.uint32(packet.cam),
            "message_id": np.uint32(packet.message_id),
            "cif0": np.uint32(packet.cif0),
            "cif2": np.uint32(packet.cif2),
            "cif4": np.uint32(packet.cif4),
            "cited_SID": np.uint32(packet.cited_sid),
            "reject_reason": np.uint32(packet.reject_reason),
            "data_addr_index": np.uint32(packet.data_addr_index),
            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),
        })

    def process(self, payload: bytes,
                *,
                frame_index: int,
                packet_index: int):
        self.__add_record(_ExtensionCommandPacket(payload),
                          frame_index=frame_index,
                          packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
