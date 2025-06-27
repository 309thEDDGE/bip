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
    ("tsi", pa.uint32()),
    ("tsf0", pa.uint32()),
    ("tsf1", pa.uint32()),
    ("time", pa.float64(), "gps"),
    ("stream_id", pa.uint32()),
    ("classId0", pa.uint32()),
    ("classId1", pa.uint32()),
    ("cif0", pa.uint32()),
    ("cif1", pa.uint32()),
    ("cif2", pa.uint32()),
    ("cif3", pa.uint32()),
    ("cif4", pa.uint32()),
    ("bandwidth", pa.float64(), "GHz"),
    ("freq", pa.float64(), "GHz"),
    ("rfFreqOffset", pa.float64(), "GHz"),
    ("gain", pa.uint32()),
    ("sampling_rate", pa.float64(), "MSps"),
    ("dwell", pa.float64(), "us"),
    ("dataFormat0", pa.uint32()),
    ("dataFormat1", pa.uint32()),
    ("polarization", pa.uint32()),
    ("azimuth", pa.float32(), "deg"),
    ("elevation", pa.float32(), "deg"),
    ("beamwidth", pa.uint32()),
    ("cited_SID", pa.uint32()),
    ("functionPriorityId", pa.uint32()),
    ("requested_input_GT", pa.uint32()),
    ("reject_reason", pa.uint32()),
    ("data_addr_index", pa.uint32()),
    ("TxDigitalInputPower", pa.uint32()),
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
class _DataContextPacket(VitaExtensionCommandPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        # Time in Juliet data is based off a custom epoch
        # Jan 1 2019 we need to add 1546300800 to bring it inline with Unix
        self.time = (bit_manipulation.time(tsi, tsf0, tsf1) + 1546300800)
        self.classId0, self.classId1 = self.class_identifier

        # missing cam from ICD, should be words[7]
        # missing messageId from ICD, should be words[8]

        self.cif0 = self.words[7]  # pick up at words[7], data matches this
        self.cif1 = self.words[8]
        self.cif2 = self.words[9]
        self.cif3 = self.words[10]
        self.cif4 = self.words[11]
        self.bandwidth = bit_manipulation.bandwidth(
            self.words[12], self.words[13])
        self.freq = bit_manipulation.frequency(self.words[14], self.words[15])
        self.rfFreqOffset = bit_manipulation.frequency(
            self.words[16], self.words[17])
        self.gain = bit_manipulation.gain(self.words[18])
        self.sampling_rate = bit_manipulation.sample_rate(
            self.words[19], self.words[20])
        self.dataFormat0 = self.words[21]
        self.dataFormat1 = self.words[22]
        self.polarization = self.words[23]
        # does not follow ICD, this byte position comes from their matlab
        # script
        self.azimuth, self.elevation = bit_manipulation.pointing_vector(
            self.words[24])
        self.beamWidth = self.words[25]
        self.cited_SID = self.words[26]
        self.functionPriorityId = self.words[27]
        # does not follow ICD, this byte position comes from ther matlab script
        self.dwell = bit_manipulation.dwell(self.words[28], self.words[29])
        self.requested_input_GT = self.words[30]
        self.reject_reason = self.words[31]
        self.data_addr_index = self.words[32]
        self.TxDigitalInputPower = self.words[33]


class DataContext:
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
                     packet: _DataContextPacket,
                     *,
                     frame_index: int,
                     packet_index: int
                     ):
        assert isinstance(packet, _DataContextPacket)
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
            "time": np.double(packet.time),
            "stream_id": np.uint32(packet.stream_id),
            "classId0": np.uint32(packet.classId0),
            "classId1": np.uint32(packet.classId1),
            "cif0": np.uint32(packet.cif0),
            "cif1": np.uint32(packet.cif1),
            "cif2": np.uint32(packet.cif2),
            "cif3": np.uint32(packet.cif3),
            "cif4": np.uint32(packet.cif4),
            "bandwidth": np.double(packet.bandwidth),
            "freq": np.double(packet.freq),
            "rfFreqOffset": np.double(packet.rfFreqOffset),
            "gain": np.uint32(packet.gain),
            "sampling_rate": np.double(packet.sampling_rate),
            "dwell": np.double(packet.dwell),
            "dataFormat0": np.uint32(packet.dataFormat0),
            "dataFormat1": np.uint32(packet.dataFormat1),
            "polarization": np.uint32(packet.polarization),
            "azimuth": np.float32(packet.azimuth),
            "elevation": np.float32(packet.elevation),
            "beamwidth": np.uint32(packet.beamWidth),
            "cited_SID": np.uint32(packet.cited_SID),
            "functionPriorityId": np.uint32(packet.functionPriorityId),
            "requested_input_GT": np.uint32(packet.requested_input_GT),
            "reject_reason": np.uint32(packet.reject_reason),
            "data_addr_index": np.uint32(packet.data_addr_index),
            "TxDigitalInputPower": np.uint32(packet.TxDigitalInputPower),
            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),
        })

    def process(self, payload: bytes,
                *,
                frame_index: int,
                packet_index: int):
        self.__add_record(_DataContextPacket(payload),
                          frame_index=frame_index,
                          packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
