from pathlib import Path

import pyarrow as pa
import numpy as np

from bip.vita import ContextPacket

UNIT_ANGLE = "rad"
UNIT_ANGLE_VEL = "rad/s"
UNIT_LEN = "m"
UNIT_VEL = "m/s"
UNIT_ACCEL = "m/s/s"

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

    ("system_status", pa.list_(pa.uint16(), -1), None),
    ("filter_status", pa.list_(pa.uint16(), -1), None),
    ("unix_time_seconds", pa.list_(pa.uint32(), -1), "sec"),
    ("microseconds", pa.list_(pa.uint32(), -1), "usec"),
    ("latitude", pa.list_(pa.float64(), -1), UNIT_ANGLE),
    ("longitude", pa.list_(pa.float64(), -1), UNIT_ANGLE),
    ("altitude", pa.list_(pa.float64(), -1), UNIT_LEN),
    ("velocity_0", pa.list_(pa.float32(), -1), UNIT_VEL),
    ("velocity_1", pa.list_(pa.float32(), -1), UNIT_VEL),
    ("velocity_2", pa.list_(pa.float32(), -1), UNIT_VEL),
    ("acceleration_0", pa.list_(pa.float32(), -1), UNIT_ACCEL),
    ("acceleration_1", pa.list_(pa.float32(), -1), UNIT_ACCEL),
    ("acceleration_2", pa.list_(pa.float32(), -1), UNIT_ACCEL),
    ("gforce", pa.list_(pa.float32(), -1), "g"),
    ("attitude_0", pa.list_(pa.float32(), -1), UNIT_ANGLE),
    ("attitude_1", pa.list_(pa.float32(), -1), UNIT_ANGLE),
    ("attitude_2", pa.list_(pa.float32(), -1), UNIT_ANGLE),
    ("attitude_rate_0", pa.list_(pa.float32(), -1), UNIT_ANGLE_VEL),
    ("attitude_rate_1", pa.list_(pa.float32(), -1), UNIT_ANGLE_VEL),
    ("attitude_rate_2", pa.list_(pa.float32(), -1), UNIT_ANGLE_VEL),
    ("latitude_std_dev", pa.list_(pa.float32(), -1), UNIT_LEN),
    ("longitude_std_dev", pa.list_(pa.float32(), -1), UNIT_LEN),
    ("altitude_std_dev", pa.list_(pa.float32(), -1), UNIT_LEN),

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


class _GPSExtensionContextPacket(ContextPacket):
    def __init__(self, payload: bytes):
        super().__init__(payload)

        assert self.class_id.information_class_code == 3
        assert self.class_id.packet_class_code == 3

        self.system_status = []
        self.filter_status = []
        self.unix_time_seconds = []
        self.microseconds = []
        self.latitude = []
        self.longitude = []
        self.altitude = []
        self.velocity_0 = []
        self.velocity_1 = []
        self.velocity_2 = []
        self.acceleration_0 = []
        self.acceleration_1 = []
        self.acceleration_2 = []
        self.gforce = []
        self.attitude_0 = []
        self.attitude_1 = []
        self.attitude_2 = []
        self.attitude_rate_0 = []
        self.attitude_rate_1 = []
        self.attitude_rate_2 = []
        self.latitude_std_dev = []
        self.longitude_std_dev = []
        self.altitude_std_dev = []

        # The GPS Context packet contains 25 navigational structures each containing the following
        # 23 fields.
        # The navigational structures appear starting at word 4 after the
        # header, stream id, and 2 word class id
        for i in range(25):
            ss, fs = self.words[(25 * i) + 4:(25 * i) + 5].view(dtype=np.int16)
            self.system_status.append(np.uint16(ss))
            self.filter_status.append(np.uint16(fs))
            self.unix_time_seconds.append(np.uint32(self.words[(25 * i) + 5]))
            self.microseconds.append(np.uint32(self.words[(25 * i) + 6]))
            self.latitude.append(np.float64(
                self.words[(25 * i) + 7:(25 * i) + 9].view(dtype=np.float64())))
            self.longitude.append(np.float64(
                self.words[(25 * i) + 9:(25 * i) + 11].view(dtype=np.float64())))
            self.altitude.append(np.float64(
                self.words[(25 * i) + 11:(25 * i) + 13].view(dtype=np.float64())))
            self.velocity_0.append(np.float32(
                self.words[(25 * i) + 13].view(dtype=np.float32())))
            self.velocity_1.append(np.float32(
                self.words[(25 * i) + 14].view(dtype=np.float32())))
            self.velocity_2.append(np.float32(
                self.words[(25 * i) + 15].view(dtype=np.float32())))
            self.acceleration_0.append(np.float32(
                self.words[(25 * i) + 16].view(dtype=np.float32())))
            self.acceleration_1.append(np.float32(
                self.words[(25 * i) + 17].view(dtype=np.float32())))
            self.acceleration_2.append(np.float32(
                self.words[(25 * i) + 18].view(dtype=np.float32())))
            self.gforce.append(np.float32(
                self.words[(25 * i) + 19].view(dtype=np.float32())))
            self.attitude_0.append(np.float32(
                self.words[(25 * i) + 20].view(dtype=np.float32())))
            self.attitude_1.append(np.float32(
                self.words[(25 * i) + 21].view(dtype=np.float32())))
            self.attitude_2.append(np.float32(
                self.words[(25 * i) + 22].view(dtype=np.float32())))
            self.attitude_rate_0.append(np.float32(
                self.words[(25 * i) + 23].view(dtype=np.float32())))
            self.attitude_rate_1.append(np.float32(
                self.words[(25 * i) + 24].view(dtype=np.float32())))
            self.attitude_rate_2.append(np.float32(
                self.words[(25 * i) + 25].view(dtype=np.float32())))
            self.latitude_std_dev.append(np.float32(
                self.words[(25 * i) + 26].view(dtype=np.float32())))
            self.longitude_std_dev.append(np.float32(
                self.words[(25 * i) + 27].view(dtype=np.float32())))
            self.altitude_std_dev.append(np.float32(
                self.words[(25 * i) + 28].view(dtype=np.float32())))


class GPSExtensionContext:
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: dict = None,
                 batch_size: int = 1,
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
                   packet: _GPSExtensionContextPacket,
                   *,
                   frame_index: int,
                   packet_index: int
                   ):
        assert isinstance(packet, _GPSExtensionContextPacket)
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

            "system_status": packet.system_status,
            "filter_status": packet.filter_status,
            "unix_time_seconds": packet.unix_time_seconds,
            "microseconds": packet.microseconds,
            "latitude": packet.latitude,
            "longitude": packet.longitude,
            "altitude": packet.altitude,
            "velocity_0": packet.velocity_0,
            "velocity_1": packet.velocity_1,
            "velocity_2": packet.velocity_2,
            "acceleration_0": packet.acceleration_0,
            "acceleration_1": packet.acceleration_1,
            "acceleration_2": packet.acceleration_2,
            "gforce": packet.gforce,
            "attitude_0": packet.attitude_0,
            "attitude_1": packet.attitude_1,
            "attitude_2": packet.attitude_2,
            "attitude_rate_0": packet.attitude_rate_0,
            "attitude_rate_1": packet.attitude_rate_1,
            "attitude_rate_2": packet.attitude_rate_2,
            "latitude_std_dev": packet.latitude_std_dev,
            "longitude_std_dev": packet.longitude_std_dev,
            "altitude_std_dev": packet.altitude_std_dev,

            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(packet_index),
        })

    def process(self, payload: bytes,
                *,
                frame_index: int,
                packet_index: int):
        self.add_record(_GPSExtensionContextPacket(payload),
                        frame_index=frame_index,
                        packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
