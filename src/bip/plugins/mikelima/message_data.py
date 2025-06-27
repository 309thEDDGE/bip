import pyarrow as pa
from pathlib import Path
import numpy as np
from bip.common import numpy_manipulation
from bip.non_vita import mblb
from . IQ0_packet_data import ProcessIq0Packet
from . IQ5_packet_data import ProcessIq5Packet

START_OF_PACKET = bytearray.fromhex(
    'F17FFF7FFF7FFF7FF17FFF7FFF7FFF7FF17FFF7FFF7FFF7F')
LANES = 3
MARKER_BYTES = 8
HEADER_BYTES = 32
MESSAGE_FILENAME = "message_content"
IQ0_PACKET_FILENAME = "iq0_packet_content"
IQ5_PACKET_FILENAME = "iq5_packet_content"

_message_schema = [
    ("IQ_type", pa.uint8()),
    ("session_id", pa.uint8()),
    ("increment", pa.uint32()),
    ("timestamp_from_filename", pa.uint64()),
    ("SOM_lane1_id", pa.uint8()),
    ("SOM_lane2_id", pa.uint8()),
    ("SOM_lane3_id", pa.uint8()),
    ("CI_number", pa.uint32()),
    ("message_key", pa.string()),
    ("SOM_message_number", pa.uint8()),
    ("SOM_SI_number", pa.uint8()),
    ("SOM_path_id", pa.uint8()),
    ("SOM_path_width", pa.uint8()),
    ("SOM_subpath_id", pa.uint8()),
    ("SOM_subpath_width", pa.uint8()),
    ("BE", pa.uint8()),
    ("Beam_select", pa.uint8()),
    ("AFS_mode", pa.uint8()),
    ("High_gain", pa.uint32()),
    ("Schedule_number", pa.uint16()),
    ("SI_in_schedule_number", pa.uint16()),
    ("Event_start_time", pa.uint64()),
    ("message_time", pa.uint64(), "us"),
    ("BTI_length", pa.uint32()),
    ("Dwell", pa.uint32(), "USec"),
    ("Frequency_Message", pa.float32(), "GHz"),
    ("Packet_Count", pa.uint16()),
    ("EOM_CI_number", pa.uint32()),
    ("Error_status", pa.uint64()),
    ("EOM_message_number", pa.uint16()),
    ("SubCCI_number", pa.uint16()),
    ("CRC", pa.uint64()),
    ("EOM_lane1_id", pa.uint16()),
    ("EOM_lane2_id", pa.uint16()),
    ("EOM_lane3_id", pa.uint16()),
    ("EOM_path_id", pa.uint16()),
    ("EOM_path_width", pa.uint16()),
    ("EOM_subpath_id", pa.uint8()),
    ("EOM_subpath_width", pa.uint8())
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


schema = [_schema_elt(e) for e in _message_schema]


class ProcessMessage:
    def __init__(self,
                 output_path: Path,
                 Recorder: type,
                 recorder_opts: dict = None,
                 batch_size: int = 100,
                 iq_type: int = 0,
                 **kwargs):
        if recorder_opts is None:
            recorder_opts = {}

        self.options = kwargs
        self.packet_id = 0

        if iq_type == 5:
            packet_data_filename = f"{IQ5_PACKET_FILENAME}.{
                Recorder.extension()}"
            self.packet_processor = ProcessIq5Packet(
                output_path / packet_data_filename,
                Recorder,
                options=recorder_opts,
                batch_size=10)
        else:
            packet_data_filename = f"{IQ0_PACKET_FILENAME}.{
                Recorder.extension()}"
            self.packet_processor = ProcessIq0Packet(
                output_path / packet_data_filename,
                Recorder,
                options=recorder_opts,
                batch_size=10)

    def process_orphan_packets(self, orphan_packet_list: list, iq_type: int,
                               session_id: int, increment: int, timestamp_from_filename: int):
        '''
        writes orphan data packets to the packet data parquet
        '''
        for packet in orphan_packet_list:
            # SOP is 3 32-byte headers
            assert packet[0:(LANES * MARKER_BYTES)] == START_OF_PACKET
            # skip the start of packet
            sop = packet[(LANES * MARKER_BYTES):(LANES * (MARKER_BYTES + HEADER_BYTES))]
            sop_obj = mblb.MblbPacket(sop)

            self.packet_processor.process_orphan_packet(
                packet,
                sop_obj,
                iq_type,
                session_id,
                increment,
                timestamp_from_filename)  # read individual packet

        return len(orphan_packet_list)

    def read_packets(self, stream: bytearray):
        '''
        Searches for the packets inside of the message body
        returns the packet list
        '''
        numpy_stream = np.array(stream, dtype=np.uint8())

        index_list = numpy_manipulation.find_subarray_indexes(
            numpy_stream, START_OF_PACKET)
        packet_list = np.split(numpy_stream, index_list)

        return packet_list[1:]

    def process_msg(self, stream: bytearray, som_obj):
        '''
        Process the message by creating a list of the packets inside of it
        returns the length of the packet list
        '''
        assert stream[0:(LANES * MARKER_BYTES)] == START_OF_PACKET

        # bytearray of the whole message
        packet_list = self.read_packets(stream)

        for count, packet in enumerate(packet_list):
            '''
            count here will give us the index, thus knowing how many dwells
            to factor into the time calculation
            '''
            packet = bytearray(packet)

            # SOP is 3 32-byte headers
            # skip the start of packet
            sop = packet[(LANES * MARKER_BYTES):(LANES * (MARKER_BYTES + HEADER_BYTES))]
            sop_obj = mblb.MblbPacket(sop)

            self.packet_processor.process_packet(
                packet, sop_obj, som_obj, count)  # read individual packet
        return len(packet_list)

    @property
    def metadata(self) -> dict:
        return self.packet_processor.metadata | {"schema": schema}
