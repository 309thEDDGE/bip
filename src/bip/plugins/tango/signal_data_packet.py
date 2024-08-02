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

    ("classid_pad_bit_count", pa.uint8(), None),
    ("classid_oui", pa.uint32(), None),
    ("classid_information_class_code", pa.uint16(), None),
    ("classid_packet_class_code", pa.uint16(), None),

    ("tsi", pa.uint32()),
    ("tsf0", pa.uint32()),
    ("tsf1", pa.uint32()),
    ("time", pa.float64(), "GPS"),

    ("stream_id", pa.uint32()),
    ("sample_count", pa.uint32()),
    ("trailer", pa.uint32()),

    ("frame_index", pa.uint32()),
    ("packet_index", pa.uint32()),

    ("samples_i", pa.list_(pa.int16(), -1)),
    ("samples_q", pa.list_(pa.int16(), -1)),
    
    ("data_key", pa.string())
]

def _schema_elt(e: tuple) -> dict:
    if len(e) > 2:
        return {
                "name": e[0],
                "type": str(e[1]),
                "unit": str(e[2]) if e[2] is not None else None
                }
    else:
        return {
                "name": e[0],
                "type": str(e[1]),
                }

schema = [ _schema_elt(e) for e in _schema ]



class _SignalDataPacket(SignalDataPacket):
    def __init__(self, payload: bytes, payload_size: int, context_key:str = "", **kwargs):
        super().__init__(payload, payload_size = payload_size, vendor = 'Tango')
        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        self.time = bit_manipulation.time(tsi, tsf0, tsf1)
        
        if ("{stream_id}" in context_key):
            self.context_packet_key = context_key.format(stream_id=self.stream_id)
        else:
            self.context_packet_key = context_key
            

class SignalData:
    def __init__(self,
            output_path: Path,
            Recorder: type,
            recorder_opts: dict = {},
            batch_size: int = 1000,
            **kwargs):

        self.recorder = Recorder(
                output_path,
                schema=pa.schema([(e[0], e[1]) for e in _schema]),
                options=recorder_opts,
                batch_size=batch_size)

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

            "classid_pad_bit_count": np.uint8(packet.class_id_codes.pad_bit_count),
            "classid_oui": np.uint32(packet.class_id_codes.oui),
            "classid_information_class_code": np.uint16(packet.class_id_codes.information_class_code),
            "classid_packet_class_code": np.uint16(packet.class_id_codes.packet_class_code),

            "tsi": np.uint32(packet.integer_timestamp),
            "tsf0": np.uint32(packet.fractional_timestamp[0]),
            "tsf1": np.uint32(packet.fractional_timestamp[1]),
            "time": np.float64(packet.time),

            "stream_id": np.uint32(packet.stream_id),
            "sample_count": np.uint32(packet.sample_count),
            "trailer": np.uint32(packet.trailer),

            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),

            "samples_i": packet.data[:,0],
            "samples_q": packet.data[:,1],
            
            "data_key": packet.context_packet_key
        })

    def process(self,
            payload: bytes,
            *,
            frame_index: int,
            packet_index: int,
            payload_size: int,
            context_packet_key: str = ""):
        #payload_size -1 since tango adds an extra trailer
        self.add_record(_SignalDataPacket(payload, payload_size, context_packet_key),
                frame_index=frame_index,
                packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict :
        return self.recorder.metadata | {"schema": schema}

