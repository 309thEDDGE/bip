from io import RawIOBase
from pathlib import Path
import os

import numpy as np
import pyarrow as pa
import logging

from bip import vita

from . __version__ import __version__ as version
from . import frame
from . signal_data_packet import SignalData
from . context_packet import Context
from . heartbeat_context_packet import HeartbeatContext
from . gps_context_packet import GPSExtensionContext
from bip.common import logger as our_logging

BAD_PACKET_STATUS_CODE = "BAD_PACKET"

FRAME_DATA_FILENAME = "framing_packets"
BAD_PACKETS_FILENAME = "bad_packets"
UNKNOWN_PACKETS_FILENAME = "unknown_packets"
SIGNAL_DATA_FILENAME = "data"
CONTEXT_FILENAME = "context"
HEARTBEAT_CONTEXT_FILENAME = "heartbeat_context"
GPS_EXTENSION_CONTEXT_FILENAME = "gps_context"

SIGNAL_DATA_PACKET = 0b0001
CONTEXT_DATA_PACKET = 0b0100
OTHER_CONTEXT_PACKETS = 0b0101

bad_packets_schema = pa.schema([
    ("frame_count", pa.uint32()),
    ("frame_size", pa.uint32()),
    ("start_bytes", pa.uint64()),
    ("frame_index", pa.uint32()),
    ("bytes", pa.list_(pa.uint32(), -1)),
    ("reason", pa.string()),
])


class Parser:
    options: dict
    _bytes_read: int
    _packets_read: int

    def __init__(self,
                 input_path: Path,
                 output_path: Path,
                 Recorder: type,
                 log_level=logging.WARNING,
                 data_recorder: type = None,
                 recorder_opts: dict = None,
                 context_key_function=None,
                 orphan_context_key: str = "ORPHAN_DATA",
                 **kwargs
                 ):

        if recorder_opts is None:
            recorder_opts = {}

        self.options = kwargs
        self.clean = False
        if kwargs.get("clean") is True:
            self.clean = True
        self._bytes_read = 0
        self._packets_read = 0
        self._frames_read = 0
        self._frame_count = 0
        self._frame_size = 0
        self._start_bytes = 0
        self._bad_packets = 0
        self._closed = False
        self._context_key_function = (
            lambda x: x) if not context_key_function else context_key_function
        self._latest_context_key = orphan_context_key

        self.logger = our_logging.create_logger(
            __name__, "TANGO", logger_level=log_level, log_dir=os.path.join(
                output_path, "bip", "logs"))

        if not data_recorder:
            data_recorder = Recorder

        frame_data_filename = f"{FRAME_DATA_FILENAME}.{Recorder.extension()}"
        self.frame_recorder = Recorder(
            output_path / frame_data_filename,
            schema=frame.schema,
            options=recorder_opts,
            batch_size=10000)
        self.options["framing_packet_data"] = {
            "filename": frame_data_filename,
        } | self.frame_recorder.metadata

        bad_packets_filename = f"{BAD_PACKETS_FILENAME}.{Recorder.extension()}"
        self.bad_packets_recorder = Recorder(
            output_path / bad_packets_filename,
            schema=bad_packets_schema,
            options=recorder_opts,
            batch_size=1)
        self.options["bad_packets_data"] = {
            "filename": bad_packets_filename,
        } | self.bad_packets_recorder.metadata

        unknown_packets_filename = f"{UNKNOWN_PACKETS_FILENAME}.{
            Recorder.extension()}"
        self.unknown_packets_recorder = Recorder(
            output_path / unknown_packets_filename,
            schema=bad_packets_schema,
            options=recorder_opts,
            batch_size=1)
        self.options["bad_packets_data"] = {
            "filename": bad_packets_filename,
        } | self.bad_packets_recorder.metadata

        signal_data_filename = f"{SIGNAL_DATA_FILENAME}.{
            data_recorder.extension()}"
        self.signal_data = SignalData(
            output_path / signal_data_filename,
            data_recorder,
            recorder_opts,
            batch_size=100,
            clean=self.clean)
        self.options["signal_data"] = {
            "filename": signal_data_filename,
        } | self.signal_data.metadata

        context_filename = f"{CONTEXT_FILENAME}.{Recorder.extension()}"
        self.context = Context(
            output_path / context_filename,
            Recorder,
            recorder_opts,
            batch_size=100,
            clean=self.clean)
        self.options["context"] = {
            "filename": context_filename,
        } | self.context.metadata

        heartbeat_context_filename = f"{HEARTBEAT_CONTEXT_FILENAME}.{
            Recorder.extension()}"
        self.heartbeat_context = HeartbeatContext(
            output_path / heartbeat_context_filename,
            Recorder,
            recorder_opts,
            batch_size=100,
            clean=self.clean)
        self.options["heartbeat_context"] = {
            "filename": heartbeat_context_filename,
        } | self.heartbeat_context.metadata

        gps_context_filename = f"{GPS_EXTENSION_CONTEXT_FILENAME}.{
            Recorder.extension()}"
        self.gps_context = GPSExtensionContext(
            output_path / gps_context_filename,
            Recorder,
            recorder_opts,
            batch_size=1,
            clean=self.clean)
        self.options["gps_context"] = {
            "filename": gps_context_filename,
        } | self.gps_context.metadata

    @property
    def metadata(self) -> dict:
        return {
            "name": "Tango parser",
            "version": version,
            "options": self.options,
            "bad packets": self._bad_packets,
        }

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def frame_size(self) -> int:
        return self._frame_size

    @property
    def start_bytes(self) -> int:
        return self._start_bytes

    @property
    def packets_read(self) -> int:
        return self._packets_read

    @property
    def bad_packets(self) -> int:
        return self._bad_packets

    def find_first_packet(self, buf: RawIOBase):
        bytes_read = frame.first_header(buf)
        self.options["first_packet_offset"] = bytes_read
        self._bytes_read = bytes_read

    def remove_deadbeef(self, payload: bytearray):
        DEADBEEF_BYTEARRAY = bytearray.fromhex("EFBEADDE")

        db_idx = payload.find(DEADBEEF_BYTEARRAY)
        new_payload = bytearray()
        if (db_idx > 0):
            self.bad_packets_recorder.add_record({
                "frame_count": np.uint32(self._frame_count),
                "frame_size": np.uint32(self._frame_size),
                "start_bytes": np.uint64(self._start_bytes),
                "frame_index": np.uint32(self._frames_read),
                "bytes": np.frombuffer(payload, count=-1, dtype=np.uint32),
                "reason": "DEADBEEF found in payload."
            })
            self.logger.info("Removing DEADBEEF from the payload...")
            new_payload.extend(payload[:db_idx])
            while db_idx > 0:
                start_search = db_idx + len(DEADBEEF_BYTEARRAY)
                db_idx = payload.find(DEADBEEF_BYTEARRAY, start_search)
                if (db_idx - start_search > 0):
                    new_payload.extend(payload[start_search:db_idx])
            new_payload.extend(payload[start_search:])
            return new_payload
        return payload

    def clean_deadbeef_for_packet(
            self, buf: RawIOBase, payload: bytearray, expected_size: int):
        total_payload_diff = 0
        payload = self.remove_deadbeef(payload)

        # If some dead beef was removed, we need to read in more data
        while (len(payload) != expected_size):
            self.logger.info(
                "Grabbing more data due to removal of DEADBEEF...")
            payload_diff = expected_size - len(payload)
            total_payload_diff += payload_diff
            additional_payload = bytearray(payload_diff)
            buf.readinto(additional_payload)
            payload.extend(additional_payload)
            payload = self.remove_deadbeef(payload)

        return payload, total_payload_diff

    def close_recorder(self):
        if self.frame_recorder.writer is not None:
            self.frame_recorder.close()

    def read_packet(self, buf: RawIOBase):
        bytes_read, header = frame.read_header(buf)
        if bytes_read == 0 or header == (0, 0):
            self.close_recorder()
            return None, None

        self._frame_count = header[0]
        self._frame_size = np.uint32(header[1])
        self._start_bytes = (self._bytes_read + bytes_read)
        starting_location = buf.tell()

        # Not counting VRLP and packet header
        FRAME_HEADER_WORDS_CNT = 2
        payload_size_words = header[1] - FRAME_HEADER_WORDS_CNT
        expected_size = 4 * payload_size_words
        payload = bytearray(expected_size)
        payload_size_bytes = buf.readinto(payload)

        total_payload_diff = 0
        if self.clean:
            payload, total_payload_diff = self.clean_deadbeef_for_packet(
                buf, payload, expected_size)

        if payload[-4:] == bytes("DNEV", encoding="ascii"):
            # This is a well-formed packet.
            self.logger.info("Found end of Frame, everything is normal...")
            self.frame_recorder.add_record({
                "frame_count": np.uint32(self._frame_count),
                "frame_size": np.uint32(self._frame_size),
                "start_bytes": np.uint64(self._start_bytes),
                "frame_index": np.uint32(self._frames_read)
            })
            self._bytes_read += (bytes_read +
                                 payload_size_bytes +
                                 total_payload_diff)

            # leave off VEND
            return payload[:-4], payload_size_words - 1

        # This is a bad packet.
        ''' From here we know the packet_size is wrong
        There are 3 possibilities
        1: We are at the end of the file
        2: Packet_size is too small
        3: packet_size is too large'''

        premature_ending = payload.find(b'DNEV')
        # This checks if we're at the end of the file
        if payload_size_bytes != expected_size:
            self._bytes_read += (bytes_read +
                                 payload_size_bytes +
                                 total_payload_diff)
            payload = payload[:payload_size_bytes]
            reason = f"incomplete read {payload_size_bytes}/{expected_size} bytes"
            self.close_recorder()
            self.logger.warning(
                f"incomplete read {payload_size_bytes}/{expected_size} bytes")

        # This checks if packet_size is too large
        elif premature_ending != -1:
            self.logger.info(
                "Found DNEV within payload, cutting the payload short to match this.")
            buf.seek(starting_location)
            reason = "Found DNEV within payload, frame size given is larger than actual frame size."
            new_payload = bytearray(premature_ending + 4)
            new_payload_size_bytes = buf.readinto(new_payload)
            self._bytes_read += (bytes_read +
                                 total_payload_diff +
                                 new_payload_size_bytes)
            payload = new_payload

        else:
            reason = "Could not find DNEV trailer, frame size given does not match data"
            # If packet_size is too small it's very annoying so true.
            while payload[-4:] != bytes("DNEV", encoding="ascii"):
                buffer_payload = bytearray(4)
                buffer_size = buf.readinto(buffer_payload)

                if buffer_size == 0:
                    self.logger.warning(
                        "Last packet has incorrect packet_size")
                    break

                payload_size_bytes += 4
                payload += buffer_payload
            self._bytes_read += (bytes_read +
                                 payload_size_bytes +
                                 total_payload_diff)

        self.bad_packets_recorder.add_record({
            "frame_count": np.uint32(self._frame_count),
            "frame_size": np.uint32(self._frame_size),
            "start_bytes": np.uint64(self._start_bytes),
            "frame_index": np.uint32(self._frames_read),
            "bytes": np.frombuffer(payload, count=-1, dtype=np.uint32),
            "reason": reason,
        })
        self._bad_packets += 1
        return BAD_PACKET_STATUS_CODE, None

    def process_packet(self, packet_type: int, class_id: int,
                       payload: bytes, payload_size: int):
        packet_class_code = int(class_id & 0xFFFF)
        info_class_code = int(class_id >> 16)

        if packet_type == SIGNAL_DATA_PACKET:
            self.signal_data.process(
                payload,
                frame_index=self._frames_read,
                packet_index=self._packets_read,
                payload_size=payload_size,
                context_packet_key=self._latest_context_key)
        elif packet_type == CONTEXT_DATA_PACKET:
            # We found a new context packet, so set the latest context key
            self._latest_context_key = self._context_key_function(
                str(self._frames_read))

            self.context.process(
                payload,
                frame_index=self._frames_read,
                packet_index=self._packets_read,
                context_packet_key=self._latest_context_key)
        elif (packet_type == OTHER_CONTEXT_PACKETS) & (info_class_code == 1) & (packet_class_code == 2):
            self.heartbeat_context.process(
                payload,
                frame_index=self._frames_read,
                packet_index=self._packets_read)
        elif (packet_type == OTHER_CONTEXT_PACKETS) & (info_class_code == 3) & (packet_class_code == 3):
            self.gps_context.process(
                payload,
                frame_index=self._frames_read,
                packet_index=self._packets_read)
        else:
            print(f"unhandled packet type: {packet_type}")
            self.unknown_packets_recorder.add_record({
                "frame_count": np.uint32(self._frame_count),
                "frame_size": np.uint32(self._frame_size),
                "start_bytes": np.uint64(self._start_bytes),
                "frame_index": np.uint32(self._frames_read),
                "bytes": np.frombuffer(payload, count=-1, dtype=np.uint32),
            })

    def parse_stream(self, stream: RawIOBase, progress_bar=None):
        self.logger.info("Starting the parsing...")

        if progress_bar is not None:
            last_read = 0

        stream.seek(0, os.SEEK_END)
        self.EOF = stream.tell()
        stream.seek(0, os.SEEK_SET)

        self.find_first_packet(stream)

        vita_payload, payload_size = self.read_packet(stream)
        while self.bytes_read < self.EOF:
            # in principle i need a second loop here because, acording to the
            # spec provided, multiple "VRT" packets can be squished inside one
            # vita 49.1 frame packet.  But each frame packet seems to only
            # contain one vita 49.2 packet + some junk that I can't make sense
            # of yet.
            self._packets_read += 1
            if vita_payload != BAD_PACKET_STATUS_CODE:
                header = vita.vrt_header(vita_payload)
                packet = vita.vrt_packet(vita_payload)
                class_id = packet.class_identifier

                self.process_packet(
                    header.packet_type,
                    class_id[1],
                    vita_payload,
                    payload_size)

            self._packets_read += 1
            self._frames_read += 1

            if progress_bar is not None:
                progress_bar.update(self.bytes_read - last_read)
                last_read = self.bytes_read
            else:
                if (self.packets_read % 1000 == 0):
                    print(f"{(self.bytes_read / self.EOF) * 100:.2f}% processed")

            vita_payload, payload_size = self.read_packet(stream)
