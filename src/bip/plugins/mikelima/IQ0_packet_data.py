from pathlib import Path
from bip.non_vita import mblb

import pyarrow as pa
import numpy as np

BEAMS = 2
LANES = 3
MARKER_BYTES = 8
HEADER_BYTES = 32

_IQ0_packet_schema = [
    ("IQ_type", pa.uint8()),
    ("session_id", pa.uint8()),
    ("increment", pa.uint32()),
    ("timestamp_from_filename", pa.uint64()),
    ("packet_number", pa.uint16()),
    ("mode_tag", pa.uint16()),
    ("CI_number", pa.uint32()),
    ("packet_size", pa.uint32()),
    ("data_fmt", pa.uint8()),
    ("event_id", pa.uint8()),
    ("message_number", pa.uint8()),
    ("subCCI_number", pa.uint8()),
    ("BTI_number", pa.uint16()),
    ("RF", pa.uint8()),
    ("CAGC", pa.uint8()),
    ("Rx_beam_id", pa.uint8()),
    ("Rx_config", pa.uint8()),
    ("sample_rate", pa.uint32(), "MSps"),
    ("channelizer_chan", pa.uint16()),
    ("DBF", pa.uint8()),
    ("routing_index", pa.uint8()),
    ("packet_lane1_id", pa.uint8()),
    ("packet_lane2_id", pa.uint8()),
    ("packet_lane3_id", pa.uint8()),
    ("path_id", pa.uint8()),
    ("path_width", pa.uint8()),
    ("subpath_id", pa.uint8()),
    ("subpath_width", pa.uint8()),
    ("DV", pa.uint8()),
    ("RS", pa.uint8()),
    ("valid_channels_beams", pa.uint8()),
    ("channels_beams_per_subpath", pa.uint8()),
    ("AFS_mode", pa.float32()),
    ("SchedNum", pa.float32()),
    ("SIinSchedNum", pa.float32()),
    ("time", pa.float64()),
    ("samples_i_left", pa.list_(pa.int16(), -1)),
    ("samples_q_left", pa.list_(pa.int16(), -1)),
    ("samples_i_right", pa.list_(pa.int16(), -1)),
    ("samples_q_right", pa.list_(pa.int16(), -1))
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


IQ0_schema = [_schema_elt(e) for e in _IQ0_packet_schema]


class ProcessIq0Packet():
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: dict = None,
                 batch_size: int = 10,
                 **kwargs):
        if recorder_opts is None:
            recorder_opts = {}

        self.options = kwargs

        self.packet_recorder = Recorder(
            output_path,
            schema=pa.schema([(e[0], e[1]) for e in _IQ0_packet_schema]),
            options=recorder_opts,
            batch_size=batch_size)

        self.packet_id = 0
        self.data = 0
        self.message_key = ''
        self.time = 0

    def __add_record(self,
                     packet: mblb.MblbPacket,
                     left_data,
                     right_data
                     ):
        '''
        Add a row to the packet_content parquet
        '''
        assert isinstance(packet, mblb.MblbPacket)

        self.packet_recorder.add_record({
            "IQ_type": np.uint8(self.iq_type),
            "session_id": np.uint8(self.session_id),
            "increment": np.uint32(self.increment),
            "timestamp_from_filename": np.uint64(self.timestamp_from_filename),
            "packet_number": np.uint16(packet.packet_number),
            "mode_tag": np.uint16(packet.mode_tag),
            "CI_number": np.uint32(packet.ci_number),
            "packet_size": np.uint32(packet.packet_size),
            "data_fmt": np.uint8(packet.data_fmt),
            "event_id": np.uint8(packet.event_id),
            "message_number": np.uint8(packet.message_number),
            "subCCI_number": np.uint8(packet.sub_cci_number),
            "BTI_number": np.uint16(packet.bti_number),
            "RF": np.uint8(packet.rf),
            "CAGC": np.uint8(packet.cagc),
            "Rx_beam_id": np.uint8(packet.rx_beam_id),
            "Rx_config": np.uint8(packet.rx_config),
            "sample_rate": np.uint32(self.sample_rate),
            "channelizer_chan": np.uint16(packet.channelizer_chan),
            "DBF": np.uint8(packet.dbf),
            "routing_index": np.uint8(packet.routing_index),
            "packet_lane1_id": np.uint8(packet.lane1_id),
            "packet_lane2_id": np.uint8(packet.lane2_id),
            "packet_lane3_id": np.uint8(packet.lane3_id),
            "path_id": np.uint8(packet.path_id),
            "path_width": np.uint8(packet.path_width),
            "subpath_id": np.uint8(packet.subpath_id),
            "subpath_width": np.uint8(packet.subpath_width),
            "DV": np.uint8(packet.dv),
            "RS": np.uint8(packet.rs),
            "valid_channels_beams": np.uint8(packet.valid_channels_beams),
            "channels_beams_per_subpath":
                np.uint8(packet.channels_beams_per_subpath),
            "AFS_mode": np.float32(self.afs_mode),
            "SchedNum": np.float32(self.sched_num),
            "SIinSchedNum": np.float32(self.si_in_sched_num),
            "time": np.float64(self.time / 1000000),  # us to s
            "samples_i_left": left_data[:, 0],
            "samples_q_left": left_data[:, 1],
            "samples_i_right": right_data[:, 0],
            "samples_q_right": right_data[:, 1]
        })

    @property
    def metadata(self) -> dict:
        return self.packet_recorder.metadata | {"schema": IQ0_schema}

    def process_orphan_packet(self, packet: bytearray, sop_obj, iq_type: int,
                              session_id: int, increment: int, timestamp_from_filename: int):
        data = np.frombuffer(packet,
                             offset=np.uint64(
                                 LANES * (MARKER_BYTES + HEADER_BYTES)),
                             count=np.uint64(
                                 (len(packet) - (LANES * (MARKER_BYTES + HEADER_BYTES))) / 2),
                             dtype=np.int16).reshape((-1, 2))
        self.time = np.nan
        self.left_data = data[::2]
        self.right_data = data[1::2]
        self.iq_type = iq_type
        self.session_id = session_id
        self.increment = increment - 1
        self.timestamp_from_filename = timestamp_from_filename
        self.sample_rate = 1280 / (2**sop_obj.rx_config)
        self.afs_mode = np.nan
        self.sched_num = np.nan
        self.si_in_sched_num = np.nan
        self.__add_record(sop_obj, self.left_data, self.right_data)

    def process_packet(self, stream: bytearray, packet,
                       som_obj, packet_list_index):
        '''
        the packet is passed in, now we stream the data (I/Q) into a
        1 dimensional array of 2 values per element (I/Q)
        The format in the word is IB QB IA QA, laid out across 64 bits with
        B the later sample and A being the earlier sample.

        we know that bytearray starts at SOP and ends
        right before the next SOP or EOM
        '''
        self.sample_rate = 1280 / (2**packet.rx_config)

        data = np.frombuffer(stream,
                             offset=np.uint64(
                                 LANES * (MARKER_BYTES + HEADER_BYTES)),
                             count=np.uint64(
                                 2 * som_obj.dwell * BEAMS * self.sample_rate),
                             dtype=np.int16).reshape((-1, 2))

        self.left_data = data[::2]
        self.right_data = data[1::2]
        self.time = som_obj.time_since_epoch_us + \
            (packet_list_index * som_obj.dwell)
        self.iq_type = som_obj.iq_type
        self.session_id = som_obj.session_id
        self.increment = som_obj.increment
        self.timestamp_from_filename = som_obj.timestamp_from_filename
        self.afs_mode = som_obj.afs_mode
        self.sched_num = som_obj.sched_num
        self.si_in_sched_num = som_obj.si_in_sched_num

        self.__add_record(packet, self.left_data, self.right_data)
