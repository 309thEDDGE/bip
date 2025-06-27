from pathlib import Path

import pyarrow as pa
import numpy as np

from bip.vita import SignalDataPacket
from bip.common import bit_manipulation

_schema = [
    ("packet_id", pa.uint32()),

    ("packet_size", pa.uint16()),
    ("packet_count", pa.uint16()),
    ("tsfd", pa.uint8()),
    ("tsid", pa.uint8()),
    ("indicators", pa.uint8()),
    ("packet_type", pa.uint8()),
    ("tsi", pa.uint32()),
    ("tsf0", pa.uint32()),
    ("tsf1", pa.uint32()),
    ("time", pa.float64(), "s"),
    ("stream_id", pa.uint32()),
    ("classId0", pa.uint32()),
    ("classId1", pa.uint32()),
    ("sample_count", pa.uint32()),
    ("trailer", pa.uint32()),
    ("frame_index", pa.uint32()),
    ("packet_index", pa.uint32()),
    ("samples_i", pa.list_(pa.int16(), -1)),
    ("samples_q", pa.list_(pa.int16(), -1))
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


class _SignalDataPacket(SignalDataPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        self.time = bit_manipulation.time(tsi, tsf0, tsf1)
        self.classId0, self.classId1 = self.class_identifier


class SignalData:
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: dict = None,
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
        self.data = 0
        self.packet_id = 0

    def add_record(self,
                   packet: _SignalDataPacket,
                   *,
                   frame_index: int,
                   packet_index: int
                   ):
        assert isinstance(packet, _SignalDataPacket)
        header = packet.packet_header

        self.recorder.add_record({
            "packet_id": np.uint32(self.packet_id),
            "packet_size": np.uint16(header.packet_size),
            "packet_count": np.uint16(header.packet_count),
            "tsfd": np.uint8(header.tsf),
            "tsid": np.uint8(header.tsi),
            "indicators": np.uint8(header.indicators),
            "packet_type": np.uint8(header.packet_type),
            "tsi": np.uint32(packet.integer_timestamp),
            "tsf0": np.uint32(packet.fractional_timestamp[0]),
            "tsf1": np.uint32(packet.fractional_timestamp[1]),
            "time": np.float64(packet.time + 1546300800),
            "stream_id": np.uint32(packet.stream_identifier),
            "classId0": np.uint32(packet.classId0),
            "classId1": np.uint32(packet.classId1),
            "sample_count": np.uint32(packet.sample_count),
            "trailer": np.uint32(packet.trailer),
            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),
            "samples_i": packet.data[:, 0],
            "samples_q": packet.data[:, 1]
        })

    def process(self,
                payload: bytes,
                *,
                frame_index: int,
                packet_index: int
                ):
        self.add_record(_SignalDataPacket(payload),
                        frame_index=frame_index,
                        packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
