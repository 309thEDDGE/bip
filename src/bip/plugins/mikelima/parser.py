from io import RawIOBase
from pathlib import Path

import numpy as np
import pyarrow as pa

from . __version__ import __version__ as version
from . import header
from . message_data import ProcessMessage
from . import message_data
from bip.non_vita import mblb

MESSAGE_FILENAME = "message_content"
PACKET_FILENAME = "packet_content"
UNHANDLED_MARKERS = [bytes.fromhex('F37FFF7FFF7FFF7F'),
                     bytes.fromhex('F77FFF7FFF7FFF7F'),
                     bytes.fromhex('F87FFF7FFF7FFF7F'),
                     bytes.fromhex('F97FFF7FFF7FFF7F'),
                     bytes.fromhex('FA7FFF7FFF7FFF7F')]
END_OF_MESSAGE_MARKER = bytes.fromhex('F27FFF7FFF7FFF7F')
START_OF_PACKET_MARKER = bytes.fromhex('F17FFF7FFF7FFF7F')
LANES = 3
MARKER_BYTES = 8
HEADER_BYTES = 32
IQ0_EOM_BYTES = 22
IQ5_EOM_BYTES = 21


class Parser:
    options: dict
    _bytes_read: int
    _packets_read: int
    _messages_read: int

    def __init__(self,
                 input_path: Path,
                 output_path: Path,
                 Recorder: type,  # class instance to be instantiated
                 log_level=None,
                 data_recorder: type = None,
                 context_key_function=None,
                 recorder_opts: dict = None,
                 **kwargs
                 ):
        if recorder_opts is None:
            recorder_opts = {}

        self._output_path = output_path
        self._recorder = Recorder
        self._recorder_options = recorder_opts

        self.options = kwargs
        self._bytes_read = 0
        self._packets_read = 0
        self._messages_read = 0
        self._message_index = 0
        self._message_key = ''
        self._timestamp = 0
        self._iq_type = 0
        self._session_id = 0
        self._increment = 0
        self._timestamp_from_filename = 0

        self._eom_length = IQ0_EOM_BYTES
        self._closed = False

    @property
    def metadata(self) -> dict:
        return {
            'name': 'MikeLima parser',
            'version': version,
            'options': self.options,
            'messages_read': self._messages_read,
        }

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    @property
    def messages_read(self) -> int:
        return self._messages_read

    @property
    def packets_read(self) -> int:
        return self._packets_read

    def initialize_message_processor(self, iq_type: int):
        message_data_filename = f"{MESSAGE_FILENAME}.{
            self._recorder.extension()}"

        self.message_processor = ProcessMessage(
            self._output_path,
            self._recorder,
            options=self._recorder_options,
            batch_size=10,
            iq_type=iq_type)
        self.options["message_data"] = {
            "filename": message_data_filename
        } | self.message_processor.metadata

        self.message_recorder = self._recorder(
            self._output_path / message_data_filename,
            schema=pa.schema([(e[0], e[1])
                             for e in message_data._message_schema]),
            options=self._recorder_options,
            batch_size=10)

    def close_recorder(self):
        if self.message_recorder is not None:
            self.message_recorder.close()

    def read_message(self, buf: RawIOBase):
        '''
        Take in 1 64-bit word at a time, looking for EOM marker

        Returns the bytearray of the entire message and the start of message
        object.

        Will raise exception if we encounter any of the unhandled markers
        '''
        header_data, bytes_read = header.read_message_header(
            buf)  # Bytearray and integer
        if bytes_read == 0:
            self.close_recorder()
            return None, None

        som_obj = mblb.MblbSOM(
            header_data,
            self._timestamp,
            self._iq_type,
            self._session_id,
            self._increment,
            self._timestamp_from_filename)
        self._message_key = som_obj.message_key

        message = bytearray(0)
        message_size = 0
        next_marker = bytearray(8)

        n_beams = 2
        eom_length = IQ0_EOM_BYTES

        if self._iq_type == 5:
            n_beams = 3
            eom_length = IQ5_EOM_BYTES

        # Look for SOP not EOM
        # read packet size of packet
        # While the last 8 bytes read are not the start of the 24 byte end of
        # message marker.
        while True:
            next_marker_length = buf.readinto(next_marker)

            if next_marker_length != 8:
                print('Message is broken: no EOM found')
                blank_end_of_message = bytearray(eom_length * 8)
                blank_eom_obj = mblb.MblbEOM(blank_end_of_message)
                self.__add_record(som_obj, blank_eom_obj)

                self._bytes_read += bytes_read + message_size
                return message, som_obj

            if next_marker in UNHANDLED_MARKERS:
                print("This bin file contains unhandled markers")
                return None, None

            if next_marker == END_OF_MESSAGE_MARKER:
                break

            message += next_marker
            message_size += next_marker_length
            if next_marker != START_OF_PACKET_MARKER:
                # These are not the bytes we're looking for.
                continue

            # The next 8 bytes are the start of the 24 byte start of packet marker.
            # 16 bytes for the packet markers for the other 2 lanes
            # plus 3 32-byte headers
            packet_header = bytearray(16 + (LANES * HEADER_BYTES))

            header_length = buf.readinto(packet_header)
            assert packet_header[0:16] == START_OF_PACKET_MARKER + \
                START_OF_PACKET_MARKER
            if header_length != (16 + (LANES * HEADER_BYTES)):
                print('Message is broken: the packet header is incomplete')
                blank_end_of_message = bytearray(24 * 8)
                blank_eom_obj = mblb.MblbEOM(blank_end_of_message)
                self.__add_record(som_obj, blank_eom_obj)

                self._bytes_read += bytes_read + message_size
                return message[:-8], som_obj
            sop_obj = mblb.MblbPacket(
                packet_header[16:(16 + (LANES * HEADER_BYTES))])

            packet_size = int(
                4 * (som_obj.dwell * (1280 / (2**sop_obj.rx_config)) * n_beams))

            packet_data = bytearray(packet_size)
            data_length = buf.readinto(packet_data)
            if data_length != packet_size:
                print('Message is broken: the packet data is incomplete')
                blank_end_of_message = bytearray(eom_length * 8)
                blank_eom_obj = mblb.MblbEOM(blank_end_of_message)
                self.__add_record(som_obj, blank_eom_obj)

                self._bytes_read += bytes_read + message_size
                return message[:-8], som_obj

            message += packet_header + packet_data
            message_size += header_length + data_length

        # Read the EOM markers for the other 2 lanes
        eom_marker = bytearray(16)
        buf.readinto(eom_marker)
        assert eom_marker == END_OF_MESSAGE_MARKER + END_OF_MESSAGE_MARKER
        # EOM is 24 8-byte WORDS
        end_of_message = bytearray(eom_length * 8)
        buf.readinto(end_of_message)
        eom_obj = mblb.MblbEOM(end_of_message)

        self.__add_record(som_obj, eom_obj)

        self._bytes_read += bytes_read + message_size + 16 + (eom_length * 8)
        return message, som_obj

    def __add_record(self,
                     message: mblb.MblbSOM,
                     end: mblb.MblbEOM
                     ):
        '''
        Add a row to the message_content parquet
        '''
        assert isinstance(message, mblb.MblbSOM)
        assert isinstance(end, mblb.MblbEOM)

        self.message_recorder.add_record({
            "IQ_type": np.uint8(message.iq_type),
            "session_id": np.uint8(message.session_id),
            "increment": np.uint32(message.increment),
            "timestamp_from_filename": np.uint64(message.timestamp_from_filename),
            "SOM_lane1_id": np.uint8(message.lane1_id),
            "SOM_lane2_id": np.uint8(message.lane2_id),
            "SOM_lane3_id": np.uint8(message.lane3_id),
            "CI_number": np.uint32(message.ci_number),
            "message_key": str(message.message_key),
            "SOM_message_number": np.uint8(message.message_number),
            "SOM_SI_number": np.uint8(message.si_number),
            "SOM_path_id": np.uint8(message.path_id),
            "SOM_path_width": np.uint8(message.path_width),
            "SOM_subpath_id": np.uint8(message.subpath_id),
            "SOM_subpath_width": np.uint8(message.subpath_width),
            "BE": np.uint8(message.be),
            "Beam_select": np.uint8(message.beam_select),
            "AFS_mode": np.uint8(message.afs_mode),
            "High_gain": np.uint32(message.high_gain),
            "Schedule_number": np.uint16(message.sched_num),
            "SI_in_schedule_number": np.uint16(message.si_in_sched_num),
            "Event_start_time": np.uint64(message.event_start_time_us),
            "message_time": np.uint64(message.time_since_epoch_us),
            "BTI_length": np.uint32(message.bti_length),
            "Dwell": np.uint32(message.dwell),
            "Frequency_Message": np.float32(message.freq_ghz),
            "Packet_Count": np.uint16(end.packet_count),
            "EOM_CI_number": np.uint32(end.ci_number),
            "Error_status": np.uint64(end.error_status),
            "EOM_message_number": np.uint16(end.message_number),
            "SubCCI_number": np.uint16(end.sub_cci_number),
            "CRC": np.uint64(end.crc),
            "EOM_lane1_id": np.uint16(end.lane1_id),
            "EOM_lane2_id": np.uint16(end.lane2_id),
            "EOM_lane3_id": np.uint16(end.lane3_id),
            "EOM_path_id": np.uint16(end.path_id),
            "EOM_path_width": np.uint16(end.path_width),
            "EOM_subpath_id": np.uint8(end.subpath_id),
            "EOM_subpath_width": np.uint8(end.subpath_width)
        })

    def parse_stream(self, stream: RawIOBase, progress_bar=None):
        '''
        Process the stream for the messages
        '''
        if progress_bar is not None:
            last_read = 0

        (
            num_bytes_read,
            orphan_packet_list,
            self._timestamp,
            self._iq_type,
            self._session_id,
            self._increment,
            self._timestamp_from_filename
        ) = header.read_first_header(
            stream)

        if self._iq_type == 5:
            self._eom_length = IQ5_EOM_BYTES

        self.initialize_message_processor(self._iq_type)

        self._bytes_read += num_bytes_read

        self.message_processor.process_orphan_packets(
            orphan_packet_list,
            self._iq_type,
            self._session_id,
            self._increment,
            self._timestamp_from_filename)

        msg_words, som_obj = self.read_message(
            stream)  # bytearray of the whole message
        while msg_words:

            num_packets = self.message_processor.process_msg(
                msg_words, som_obj)  # break into packets
            self._messages_read += 1
            self._packets_read += num_packets
            if progress_bar is not None:
                progress_bar.update(self._bytes_read - last_read)
                last_read = self._bytes_read

            msg_words, som_obj = self.read_message(stream)
