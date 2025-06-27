from io import RawIOBase
from pathlib import Path
import traceback
import logging

import numpy as np
import pyarrow as pa


from bip import vita
from . __version__ import __version__ as version
from . import frame
from . signal_data_packet import SignalData
from . extension_command_packet import ExtensionCommand
from . ackR_packet import AckR_Packet
from . data_context_packet import DataContext


BAD_PACKET_STATUS_CODE = "DEADBEEF"

BAD_PACKETS_FILENAME = "bad_packets"
UNKNOWN_DATA_FILENAME = "unknown_packets"
FRAME_DATA_FILENAME = "framing_packets"
SIGNAL_DATA_FILENAME = "data"
EXTENSION_COMMAND_DATA_FILENAME = "extension_command"
ACKR_DATA_FILENAME = "ackr"
CONTEXT_DATA_FILENAME = "context_data"

SIGNAL_DATA_PACKET = 0b0001
CONTEXT_DATA_PACKET = 0b0101
COMMAND_PACKET = 0b0111
EXTENSION_COMMAND_PACKET = 0b0000
ACK_DATA_PACKET = 0b0100

bad_packets_schema = pa.schema([
    ("start_bytes", pa.uint64()),
    ("bytes", pa.list_(pa.uint32(), -1)),
])

unknown_packets_schema = pa.schema([
    ("start_bytes", pa.uint64()),
    ("bytes", pa.list_(pa.uint32(), -1)),
])


class Parser:
    options: dict
    _bytes_read: int
    _packets_read: int

    def __init__(self,
                 input_path: Path,
                 output_path: Path,
                 Recorder: type,  # class instance to be instantiated
                 log_level=logging.WARNING,
                 data_recorder: type = None,
                 recorder_opts: dict = None,
                 context_key_function=None,  # TODO: Implement data partitioning
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

        self._bad_packets = 0
        self._unknown_packets = 0
        self._closed = False

        framing_data_filename = f"{FRAME_DATA_FILENAME}.{Recorder.extension()}"
        self.recorder = Recorder(
            output_path / framing_data_filename,
            schema=frame.schema,
            options=recorder_opts,
            batch_size=10000)
        self.options["framing_packet_data"] = {
            "filename": framing_data_filename
        } | self.recorder.metadata

        bad_packets_filename = f"{BAD_PACKETS_FILENAME}.{Recorder.extension()}"
        self.bad_packets_recorder = Recorder(
            output_path / bad_packets_filename,
            schema=bad_packets_schema,
            options=recorder_opts,
            batch_size=1)
        self.options["bad_packets_data"] = {
            "filename": bad_packets_filename,
        } | self.bad_packets_recorder.metadata

        unknown_packets_filename = f"{UNKNOWN_DATA_FILENAME}.{
            Recorder.extension()}"
        self.unknown_packets_recorder = Recorder(
            output_path / unknown_packets_filename,
            schema=unknown_packets_schema,
            options=recorder_opts,
            batch_size=1000)
        self.options["unknown_packets_data"] = {
            "filename": unknown_packets_filename,
        } | self.unknown_packets_recorder.metadata

        signal_data_filename = f"{SIGNAL_DATA_FILENAME}.{Recorder.extension()}"
        self.signal_data = SignalData(
            output_path / signal_data_filename,
            Recorder,
            recorder_opts,
            batch_size=1000,
            clean=self.clean)
        self.options["signal_data"] = {
            "filename": signal_data_filename,
        } | self.signal_data.metadata

        extension_command_data_filename = f"{EXTENSION_COMMAND_DATA_FILENAME}.{
            Recorder.extension()}"
        self.extension_command_data = ExtensionCommand(
            output_path / extension_command_data_filename,
            Recorder,
            recorder_opts,
            batch_size=1000,
            clean=self.clean)
        self.options["extension_command_data"] = {
            "filename": extension_command_data_filename,
        } | self.extension_command_data.metadata

        ackr_data_filename = f"{ACKR_DATA_FILENAME}.{Recorder.extension()}"
        self.ackr_data = AckR_Packet(
            output_path / ackr_data_filename,
            Recorder,
            recorder_opts,
            batch_size=1000,
            clean=self.clean)
        self.options["ackr_data"] = {
            "filename": ackr_data_filename,
        } | self.ackr_data.metadata

        context_data_filename = f"{CONTEXT_DATA_FILENAME}.{
            Recorder.extension()}"
        self.context_data = DataContext(
            output_path / context_data_filename,
            Recorder,
            recorder_opts,
            batch_size=1000,
            clean=self.clean)
        self.options["context_data"] = {
            "filename": context_data_filename,
        } | self.context_data.metadata

    @property
    def metadata(self) -> dict:
        return {
            'name': 'Juliet parser',
            'version': version,
            'options': self.options,
            'bad packets': self._bad_packets,
            'unknown packets': self._unknown_packets
        }

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    @property
    def packets_read(self) -> int:
        return self._packets_read

    @property
    def bad_packets(self) -> int:
        return self._bad_packets

    @property
    def unknown_packets(self) -> int:
        return self._unknown_packets

    def read_packet(self, buf: RawIOBase):
        bytes_read, header = frame.read_header(buf)
        if bytes_read == 0:
            if self.recorder.writer is not None:
                self.recorder.close()
            return None
        if header[0] == 0 and header[1] == 0:
            if self.recorder.writer is not None:
                self.recorder.close()
            return None

        assert header[1] > 0

        start_bytes = (self._bytes_read + bytes_read)
        # Header[1] is the size of the payload in 4-byte words
        expected_size = 4 * header[1]
        payload = bytearray(expected_size)
        payload_size = buf.readinto(payload)

        # byteswap below, takes the big endian payload and converts to little endian,
        # for our system hardware, and sanity.
        np.frombuffer(payload, dtype=np.uint32).byteswap(inplace=True)
        pkt_header = vita.vrt_header(payload)
        packet_type = pkt_header.packet_type
        indicators = pkt_header.indicators

        if (payload_size != expected_size):
            self.bad_packets_recorder.add_record({
                "start_bytes": np.uint64(start_bytes),
                "bytes": np.frombuffer(payload, count=-1, dtype=np.uint32),
            })
            self._bytes_read += (bytes_read + payload_size)
            self._bad_packets += 1
            self._packets_read += 1
            raise RuntimeError(
                f"incomplete packet: {payload_size}/{expected_size} bytes")
        elif (packet_type == CONTEXT_DATA_PACKET or packet_type == SIGNAL_DATA_PACKET or
              (packet_type == COMMAND_PACKET and indicators == EXTENSION_COMMAND_PACKET) or
              (packet_type == COMMAND_PACKET and indicators ==
               ACK_DATA_PACKET and len(payload) == 60)
              ):
            self.recorder.add_record({
                "time_ns": np.uint64(header[0]),
                "word_count": np.uint32(header[1]),
            })
            self._packets_read += 1
            self._bytes_read += (bytes_read + payload_size)
            return payload
        else:
            print(
                f"unexpected packet type - {packet_type}:{indicators}:{len(payload)}")
            self.unknown_packets_recorder.add_record({
                "start_bytes": np.uint64(start_bytes),
                "bytes": np.frombuffer(payload, count=-1, dtype=np.uint32),
            })
            self._unknown_packets += 1
            self._packets_read += 1
            self._bytes_read += (bytes_read + payload_size)
            return payload

    def process_packet(self, packet_type: int,
                       indicators: int, payload: bytes):
        # data is framed 1 frame per vita 49.2 packet
        # so frame_index and packet_index are the same
        if packet_type == SIGNAL_DATA_PACKET:
            self.signal_data.process(payload,
                                     frame_index=self._packets_read,
                                     packet_index=self._packets_read)
        elif packet_type == COMMAND_PACKET:
            if indicators == EXTENSION_COMMAND_PACKET:
                self.extension_command_data.process(payload,
                                                    frame_index=self._packets_read,
                                                    packet_index=self._packets_read)
            elif indicators == ACK_DATA_PACKET:
                if len(payload) == (9 * 4):
                    print("AckX not implemented")
                elif len(payload) == (15 * 4):
                    self.ackr_data.process(payload,
                                           frame_index=self._packets_read,
                                           packet_index=self._packets_read)
                else:
                    print("Unsupported Packet Type")
        elif packet_type == CONTEXT_DATA_PACKET:
            self.context_data.process(payload,
                                      frame_index=self._packets_read,
                                      packet_index=self._packets_read)

        else:
            print(f"unexpected packet type {packet_type:#06b}")

    def parse_stream(self, stream: RawIOBase, progress_bar=None):
        if progress_bar is not None:
            last_read = 0

        vita_payload = self.read_packet(stream)
        while vita_payload:
            header = vita.vrt_header(vita_payload)
            self.process_packet(
                header.packet_type,
                header.indicators,
                vita_payload)
            if progress_bar is not None:
                progress_bar.update(self.bytes_read - last_read)
                last_read = self.bytes_read

            try:
                vita_payload = self.read_packet(stream)
            except BaseException:
                print(traceback.format_exc())
                vita_payload = None
