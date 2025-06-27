from pathlib import Path

import pyarrow as pa
import numpy as np

from bip.vita import ContextPacket
from bip.common import bit_manipulation

_schema = [
    ("packet_id", pa.uint32(), None),

    ("packet_size", pa.uint16(), None),
    ("packet_count", pa.uint16(), None),
    ("tsfd", pa.uint8(), None),
    ("tsid", pa.uint8(), None),
    ("indicators", pa.uint8(), None),
    ("packet_type", pa.uint8(), None),

    ("classid_pad_bit_count", pa.uint8(), None),
    ("classid_oui", pa.uint32(), None),
    ("classid_information_class_code", pa.uint16(), None),
    ("classid_packet_class_code", pa.uint16(), None),

    ("tsi", pa.uint32(), None),
    ("tsf0", pa.uint32(), None),
    ("tsf1", pa.uint32(), None),
    ("time", pa.float64(), "gps"),

    ("tx_buffer_free_0", pa.uint32(), None),
    ("tx_buffer_free_1", pa.uint32(), None),
    ("tx_buffer_free_2", pa.uint32(), None),
    ("tx_buffer_free_3", pa.uint32(), None),
    ("tx_buffer_free_4", pa.uint32(), None),
    ("tx_buffer_free_5", pa.uint32(), None),
    ("tx_buffer_free_6", pa.uint32(), None),
    ("tx_buffer_free_7", pa.uint32(), None),
    ("tx_buffer_free_8", pa.uint32(), None),
    ("tx_buffer_free_9", pa.uint32(), None),
    ("tx_buffer_free_10", pa.uint32(), None),
    ("tx_buffer_free_11", pa.uint32(), None),
    ("tx_buffer_free_12", pa.uint32(), None),
    ("tx_buffer_free_13", pa.uint32(), None),
    ("tx_buffer_free_14", pa.uint32(), None),
    ("tx_buffer_free_15", pa.uint32(), None),

    ("rx_buffer_free_0", pa.uint32(), None),
    ("rx_buffer_free_1", pa.uint32(), None),
    ("rx_buffer_free_2", pa.uint32(), None),
    ("rx_buffer_free_3", pa.uint32(), None),
    ("rx_buffer_free_4", pa.uint32(), None),
    ("rx_buffer_free_5", pa.uint32(), None),
    ("rx_buffer_free_6", pa.uint32(), None),
    ("rx_buffer_free_7", pa.uint32(), None),
    ("rx_buffer_free_8", pa.uint32(), None),
    ("rx_buffer_free_9", pa.uint32(), None),
    ("rx_buffer_free_10", pa.uint32(), None),
    ("rx_buffer_free_11", pa.uint32(), None),
    ("rx_buffer_free_12", pa.uint32(), None),
    ("rx_buffer_free_13", pa.uint32(), None),
    ("rx_buffer_free_14", pa.uint32(), None),
    ("rx_buffer_free_15", pa.uint32(), None),

    ("tx_stream_id_0", pa.uint32(), None),
    ("tx_stream_id_1", pa.uint32(), None),
    ("tx_stream_id_2", pa.uint32(), None),
    ("tx_stream_id_3", pa.uint32(), None),
    ("tx_stream_id_4", pa.uint32(), None),
    ("tx_stream_id_5", pa.uint32(), None),
    ("tx_stream_id_6", pa.uint32(), None),
    ("tx_stream_id_7", pa.uint32(), None),
    ("tx_stream_id_8", pa.uint32(), None),
    ("tx_stream_id_9", pa.uint32(), None),
    ("tx_stream_id_10", pa.uint32(), None),
    ("tx_stream_id_11", pa.uint32(), None),
    ("tx_stream_id_12", pa.uint32(), None),
    ("tx_stream_id_13", pa.uint32(), None),
    ("tx_stream_id_14", pa.uint32(), None),
    ("tx_stream_id_15", pa.uint32(), None),

    ("rx_stream_id_0", pa.uint32(), None),
    ("rx_stream_id_1", pa.uint32(), None),
    ("rx_stream_id_2", pa.uint32(), None),
    ("rx_stream_id_3", pa.uint32(), None),
    ("rx_stream_id_4", pa.uint32(), None),
    ("rx_stream_id_5", pa.uint32(), None),
    ("rx_stream_id_6", pa.uint32(), None),
    ("rx_stream_id_7", pa.uint32(), None),
    ("rx_stream_id_8", pa.uint32(), None),
    ("rx_stream_id_9", pa.uint32(), None),
    ("rx_stream_id_10", pa.uint32(), None),
    ("rx_stream_id_11", pa.uint32(), None),
    ("rx_stream_id_12", pa.uint32(), None),
    ("rx_stream_id_13", pa.uint32(), None),
    ("rx_stream_id_14", pa.uint32(), None),
    ("rx_stream_id_15", pa.uint32(), None),

    ("system_time", pa.float64(), "nsec"),

    ("frame_index", pa.uint32(), None),
    ("packet_index", pa.uint32(), None),
]


def _schema_elt(e: tuple) -> dict:
    return {
        "name": e[0],
        "type": str(e[1]),
        "unit": str(e[2]) if e[2] is not None else None
    }


schema = [_schema_elt(e) for e in _schema]


class _HeartbeatContextPacket(ContextPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

        assert self.class_id.information_class_code == 1
        assert self.class_id.packet_class_code == 2

        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        self.time = bit_manipulation.time(tsi, tsf0, tsf1)

        self.tx_buffer_free_0 = int(self.words[7])
        self.tx_buffer_free_1 = int(self.words[8])
        self.tx_buffer_free_2 = int(self.words[9])
        self.tx_buffer_free_3 = int(self.words[10])
        self.tx_buffer_free_4 = int(self.words[11])
        self.tx_buffer_free_5 = int(self.words[12])
        self.tx_buffer_free_6 = int(self.words[13])
        self.tx_buffer_free_7 = int(self.words[14])
        self.tx_buffer_free_8 = int(self.words[15])
        self.tx_buffer_free_9 = int(self.words[16])
        self.tx_buffer_free_10 = int(self.words[17])
        self.tx_buffer_free_11 = int(self.words[18])
        self.tx_buffer_free_12 = int(self.words[19])
        self.tx_buffer_free_13 = int(self.words[20])
        self.tx_buffer_free_14 = int(self.words[21])
        self.tx_buffer_free_15 = int(self.words[22])

        self.rx_buffer_free_0 = int(self.words[23])
        self.rx_buffer_free_1 = int(self.words[24])
        self.rx_buffer_free_2 = int(self.words[25])
        self.rx_buffer_free_3 = int(self.words[26])
        self.rx_buffer_free_4 = int(self.words[27])
        self.rx_buffer_free_5 = int(self.words[28])
        self.rx_buffer_free_6 = int(self.words[29])
        self.rx_buffer_free_7 = int(self.words[30])
        self.rx_buffer_free_8 = int(self.words[31])
        self.rx_buffer_free_9 = int(self.words[32])
        self.rx_buffer_free_10 = int(self.words[33])
        self.rx_buffer_free_11 = int(self.words[34])
        self.rx_buffer_free_12 = int(self.words[35])
        self.rx_buffer_free_13 = int(self.words[36])
        self.rx_buffer_free_14 = int(self.words[37])
        self.rx_buffer_free_15 = int(self.words[38])

        self.tx_stream_id_0 = int(self.words[39])
        self.tx_stream_id_1 = int(self.words[40])
        self.tx_stream_id_2 = int(self.words[41])
        self.tx_stream_id_3 = int(self.words[42])
        self.tx_stream_id_4 = int(self.words[43])
        self.tx_stream_id_5 = int(self.words[44])
        self.tx_stream_id_6 = int(self.words[45])
        self.tx_stream_id_7 = int(self.words[46])
        self.tx_stream_id_8 = int(self.words[47])
        self.tx_stream_id_9 = int(self.words[48])
        self.tx_stream_id_10 = int(self.words[49])
        self.tx_stream_id_11 = int(self.words[50])
        self.tx_stream_id_12 = int(self.words[51])
        self.tx_stream_id_13 = int(self.words[52])
        self.tx_stream_id_14 = int(self.words[53])
        self.tx_stream_id_15 = int(self.words[54])

        self.rx_stream_id_0 = int(self.words[55])
        self.rx_stream_id_1 = int(self.words[56])
        self.rx_stream_id_2 = int(self.words[57])
        self.rx_stream_id_3 = int(self.words[58])
        self.rx_stream_id_4 = int(self.words[59])
        self.rx_stream_id_5 = int(self.words[60])
        self.rx_stream_id_6 = int(self.words[61])
        self.rx_stream_id_7 = int(self.words[62])
        self.rx_stream_id_8 = int(self.words[63])
        self.rx_stream_id_9 = int(self.words[64])
        self.rx_stream_id_10 = int(self.words[65])
        self.rx_stream_id_11 = int(self.words[66])
        self.rx_stream_id_12 = int(self.words[67])
        self.rx_stream_id_13 = int(self.words[68])
        self.rx_stream_id_14 = int(self.words[69])
        self.rx_stream_id_15 = int(self.words[70])

        self.system_time = float(self.words[71:73].view(dtype=np.float64))


class HeartbeatContext:
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: dict = None,
                 batch_size: int = 1000,
                 **kwargs):

        if recorder_opts is None:
            recorder_opts = {}

        self.recorder = Recorder(
            output_path,
            schema=pa.schema([(e[0], e[1]) for e in _schema]),
            options=recorder_opts,
            batch_size=batch_size)

        self.packet_id = 0

    def add_record(self,
                   packet: _HeartbeatContextPacket,
                   *,
                   frame_index: int,
                   packet_index: int
                   ):
        assert isinstance(packet, _HeartbeatContextPacket)
        header = packet.packet_header

        self.recorder.add_record({
            "packet_id": np.uint32(self.packet_id),

            "packet_size": np.uint16(header.packet_size),
            "packet_count": np.uint16(header.packet_count),
            "tsfd": np.uint8(header.tsf),
            "tsid": np.uint8(header.tsi),
            "indicators": np.uint8(header.indicators),
            "packet_type": np.uint8(header.packet_type),

            "classid_pad_bit_count": np.uint8(packet.class_id.pad_bit_count),
            "classid_oui": np.uint32(packet.class_id.oui),
            "classid_information_class_code": np.uint16(packet.class_id.information_class_code),
            "classid_packet_class_code": np.uint16(packet.class_id.packet_class_code),

            "tsi": np.uint32(packet.integer_timestamp),
            "tsf0": np.uint32(packet.fractional_timestamp[0]),
            "tsf1": np.uint32(packet.fractional_timestamp[1]),
            "time": np.float64(packet.time),

            "tx_buffer_free_0": np.uint32(packet.tx_buffer_free_0),
            "tx_buffer_free_1": np.uint32(packet.tx_buffer_free_1),
            "tx_buffer_free_2": np.uint32(packet.tx_buffer_free_2),
            "tx_buffer_free_3": np.uint32(packet.tx_buffer_free_3),
            "tx_buffer_free_4": np.uint32(packet.tx_buffer_free_4),
            "tx_buffer_free_5": np.uint32(packet.tx_buffer_free_5),
            "tx_buffer_free_6": np.uint32(packet.tx_buffer_free_6),
            "tx_buffer_free_7": np.uint32(packet.tx_buffer_free_7),
            "tx_buffer_free_8": np.uint32(packet.tx_buffer_free_8),
            "tx_buffer_free_9": np.uint32(packet.tx_buffer_free_9),
            "tx_buffer_free_10": np.uint32(packet.tx_buffer_free_10),
            "tx_buffer_free_11": np.uint32(packet.tx_buffer_free_11),
            "tx_buffer_free_12": np.uint32(packet.tx_buffer_free_12),
            "tx_buffer_free_13": np.uint32(packet.tx_buffer_free_13),
            "tx_buffer_free_14": np.uint32(packet.tx_buffer_free_14),
            "tx_buffer_free_15": np.uint32(packet.tx_buffer_free_15),

            "rx_buffer_free_0": np.uint32(packet.rx_buffer_free_0),
            "rx_buffer_free_1": np.uint32(packet.rx_buffer_free_1),
            "rx_buffer_free_2": np.uint32(packet.rx_buffer_free_2),
            "rx_buffer_free_3": np.uint32(packet.rx_buffer_free_3),
            "rx_buffer_free_4": np.uint32(packet.rx_buffer_free_4),
            "rx_buffer_free_5": np.uint32(packet.rx_buffer_free_5),
            "rx_buffer_free_6": np.uint32(packet.rx_buffer_free_6),
            "rx_buffer_free_7": np.uint32(packet.rx_buffer_free_7),
            "rx_buffer_free_8": np.uint32(packet.rx_buffer_free_8),
            "rx_buffer_free_9": np.uint32(packet.rx_buffer_free_9),
            "rx_buffer_free_10": np.uint32(packet.rx_buffer_free_10),
            "rx_buffer_free_11": np.uint32(packet.rx_buffer_free_11),
            "rx_buffer_free_12": np.uint32(packet.rx_buffer_free_12),
            "rx_buffer_free_13": np.uint32(packet.rx_buffer_free_13),
            "rx_buffer_free_14": np.uint32(packet.rx_buffer_free_14),
            "rx_buffer_free_15": np.uint32(packet.rx_buffer_free_15),

            "tx_stream_id_0": np.uint32(packet.tx_stream_id_0),
            "tx_stream_id_1": np.uint32(packet.tx_stream_id_1),
            "tx_stream_id_2": np.uint32(packet.tx_stream_id_2),
            "tx_stream_id_3": np.uint32(packet.tx_stream_id_3),
            "tx_stream_id_4": np.uint32(packet.tx_stream_id_4),
            "tx_stream_id_5": np.uint32(packet.tx_stream_id_5),
            "tx_stream_id_6": np.uint32(packet.tx_stream_id_6),
            "tx_stream_id_7": np.uint32(packet.tx_stream_id_7),
            "tx_stream_id_8": np.uint32(packet.tx_stream_id_8),
            "tx_stream_id_9": np.uint32(packet.tx_stream_id_9),
            "tx_stream_id_10": np.uint32(packet.tx_stream_id_10),
            "tx_stream_id_11": np.uint32(packet.tx_stream_id_11),
            "tx_stream_id_12": np.uint32(packet.tx_stream_id_12),
            "tx_stream_id_13": np.uint32(packet.tx_stream_id_13),
            "tx_stream_id_14": np.uint32(packet.tx_stream_id_14),
            "tx_stream_id_15": np.uint32(packet.tx_stream_id_15),

            "rx_stream_id_0": np.uint32(packet.rx_stream_id_0),
            "rx_stream_id_1": np.uint32(packet.rx_stream_id_1),
            "rx_stream_id_2": np.uint32(packet.rx_stream_id_2),
            "rx_stream_id_3": np.uint32(packet.rx_stream_id_3),
            "rx_stream_id_4": np.uint32(packet.rx_stream_id_4),
            "rx_stream_id_5": np.uint32(packet.rx_stream_id_5),
            "rx_stream_id_6": np.uint32(packet.rx_stream_id_6),
            "rx_stream_id_7": np.uint32(packet.rx_stream_id_7),
            "rx_stream_id_8": np.uint32(packet.rx_stream_id_8),
            "rx_stream_id_9": np.uint32(packet.rx_stream_id_9),
            "rx_stream_id_10": np.uint32(packet.rx_stream_id_10),
            "rx_stream_id_11": np.uint32(packet.rx_stream_id_11),
            "rx_stream_id_12": np.uint32(packet.rx_stream_id_12),
            "rx_stream_id_13": np.uint32(packet.rx_stream_id_13),
            "rx_stream_id_14": np.uint32(packet.rx_stream_id_14),
            "rx_stream_id_15": np.uint32(packet.rx_stream_id_15),

            "system_time": np.float64(packet.system_time),

            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),
        })

    def process(self, payload: bytes,
                *,
                frame_index: int,
                packet_index: int):

        self.add_record(_HeartbeatContextPacket(payload),
                        frame_index=frame_index,
                        packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
