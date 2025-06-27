import numpy as np
import uuid


class MblbSOM:

    clocks_per_us = 160  # hardcoded, source unknown

    def __init__(self, payload: bytes, timestamp: int, iq_type: int,
                 session_id: int, increment: int, timestamp_from_filename: int):
        self._payload = payload
        self._timestamp = timestamp
        self._iq_type = iq_type
        self._session_id = session_id
        self._increment = increment
        self._timestamp_from_filename = timestamp_from_filename
        self._words = np.frombuffer(self._payload, dtype=np.uint64)
        self._uuid = uuid.uuid4().hex

    @property
    def iq_type(self) -> int:
        return self._iq_type

    @property
    def session_id(self) -> int:
        return self._session_id

    @property
    def increment(self) -> int:
        return self._increment

    @property
    def timestamp_from_filename(self) -> int:
        return self._timestamp_from_filename

    @property
    def lane1_id(self) -> int:
        return (self._words[0] & 0xFF00000000000000) >> np.uint64(56)

    @property
    def lane2_id(self) -> int:
        return (self._words[1] & 0xFF00000000000000) >> np.uint64(56)

    @property
    def lane3_id(self) -> int:
        return (self._words[2] & 0xFF00000000000000) >> np.uint64(56)

    @property
    def ci_number(self) -> int:
        return self._words[0] & np.uint64(0x00000000FFFFFFFF)

    @property
    def message_key(self) -> str:
        return self._uuid

    @property
    def message_number(self) -> int:
        return (self._words[3] & np.uint64(0x000000000000FF00)) >> np.uint64(8)

    @property
    def si_number(self) -> int:
        return self._words[3] & np.uint64(0x00000000000000FF)

    @property
    def path_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x00FF000000000000)) >> np.uint64(48)

    @property
    def path_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000FF0000000000)) >> np.uint64(40)

    @property
    def subpath_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x000000F000000000)) >> np.uint64(36)

    @property
    def subpath_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000F00000000)) >> np.uint64(32)

    @property
    def be(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000080000000)) >> np.uint64(31)

    @property
    def beam_select(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000060000000)) >> np.uint64(29)

    @property
    def afs_mode(self) -> int:
        return (self._words[9] & np.uint64(
            0x000000001E000000)) >> np.uint64(25)

    @property
    def sched_num(self) -> int:
        return (self._words[12] & np.uint64(
            0x00000000FFFF0000)) >> np.uint64(16)

    @property
    def si_in_sched_num(self) -> int:
        return self._words[12] & np.uint64(0x000000000000FFFF)

    @property
    def high_gain(self) -> int:
        return (self._words[12] & np.uint64(
            0xFFFFFFFF00000000)) >> np.uint64(32)

    @property
    def event_start_time_us(self) -> int:
        back_half = (self._words[13] & np.uint64(
            0x00000000FFFFFFFF)) << np.uint64(32)
        front_half = (self._words[13] & np.uint64(
            0xFFFFFFFF00000000)) >> np.uint64(32)
        return (back_half + front_half) / MblbSOM.clocks_per_us

    @property
    def time_since_epoch_us(self) -> int:
        return self.event_start_time_us + self._timestamp

    @property
    def bti_length(self) -> int:
        return ((self._words[14] & np.uint64(0xFFFFFFFF00000000))
                >> np.uint64(32)) / MblbSOM.clocks_per_us

    @property
    def dwell(self) -> int:
        return (self._words[14] & np.uint64(
            0x00000000FFFFFFFF)) / MblbSOM.clocks_per_us

    @property
    def freq_ghz(self) -> float:
        fs = 2560 * 16  # MHz
        fine_tune_lsb_mhz = 0.625  # MHz
        ct_step = fs / 128  # 320 MHz

        ct = int(self._words[15] & np.uint64(0x00000000FFFFFFFF))
        ft = int((self._words[15] & np.uint64(
            0xFFFFFFFF00000000)) >> np.uint64(32))

        fine_tune_mhz = ft * fine_tune_lsb_mhz

        ctf = (2**7 - ct)
        cal_ct = (ctf + 1) / 3
        coarse_tune_mhz = cal_ct * ct_step * 3 - ct_step

        return (coarse_tune_mhz + fine_tune_mhz) / 1000


class MblbPacket:
    def __init__(self, payload: bytes):
        self._payload = payload
        self._words = np.frombuffer(self._payload, dtype=np.uint64)

    @property
    def packet_number(self):
        return (self._words[0] & np.uint64(
            0xFFFF000000000000)) >> np.uint64(48)

    @property
    def mode_tag(self):
        return (self._words[0] & np.uint64(
            0x0000FFFF00000000)) >> np.uint64(32)

    @property
    def ci_number(self):
        return self._words[0] & np.uint64(0x00000000FFFFFFFF)

    @property
    def packet_size(self):
        return (self._words[3] & np.uint64(
            0xFFFFFFFF00000000)) >> np.uint64(32)

    @property
    def data_fmt(self):
        return (self._words[3] & np.uint64(
            0x00000000FF000000)) >> np.uint64(24)

    @property
    def event_id(self):
        return (self._words[3] & np.uint64(
            0x0000000000FF0000)) >> np.uint64(16)

    @property
    def message_number(self):
        return (self._words[3] & np.uint64(0x000000000000FF00)) >> np.uint64(8)

    @property
    def sub_cci_number(self):
        return self._words[3] & np.uint64(0x00000000000000FF)

    @property
    def bti_number(self):
        return (self._words[6] & np.uint64(
            0xFFFF000000000000)) >> np.uint64(48)

    @property
    def rf(self):
        return (self._words[6] & np.uint64(
            0x0000FFC000000000)) >> np.uint64(38)

    @property
    def cagc(self):
        return (self._words[6] & np.uint64(
            0x0000003F00000000)) >> np.uint64(28)

    @property
    def rx_beam_id(self):
        return (self._words[6] & np.uint64(
            0x00000000FF000000)) >> np.uint64(24)

    @property
    def rx_config(self):
        return (self._words[6] & np.uint64(
            0x0000000000FC0000)) >> np.uint64(18)

    @property
    def channelizer_chan(self):
        return (self._words[6] & np.uint64(
            0x000000000003F000)) >> np.uint64(12)

    @property
    def dbf(self):
        return (self._words[6] & np.uint64(0x0000000000000F00)) >> np.uint64(8)

    @property
    def routing_index(self):
        return self._words[6] & np.uint64(0x00000000000000FF)

    @property
    def lane1_id(self):
        return (self._words[9] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def lane2_id(self):
        return (self._words[10] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def lane3_id(self):
        return (self._words[11] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def path_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x00FF000000000000)) >> np.uint64(48)

    @property
    def path_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000FF0000000000)) >> np.uint64(40)

    @property
    def subpath_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x000000F000000000)) >> np.uint64(36)

    @property
    def subpath_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000F00000000)) >> np.uint64(32)

    @property
    def dv(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000080000000)) >> np.uint64(31)

    @property
    def rs(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000060000000)) >> np.uint64(30)

    @property
    def valid_channels_beams(self) -> int:
        return (self._words[9] & np.uint64(0x000000000000FF00)) >> np.uint64(8)

    @property
    def channels_beams_per_subpath(self) -> int:
        return self._words[9] & np.uint64(0x00000000000000FF)


class MblbEOM:
    def __init__(self, payload: bytes):
        self._payload = payload
        self._words = np.frombuffer(self._payload, dtype=np.uint64)

    @property
    def packet_count(self) -> int:
        return (self._words[0] & np.uint64(
            0xFFFF000000000000)) >> np.uint64(48)

    @property
    def ci_number(self) -> int:
        return self._words[0] & np.uint64(0x00000000FFFFFFFF)

    @property
    def error_status(self) -> int:
        return (self._words[1] & np.uint64(
            0xFFFFFFFFFFFF0000)) >> np.uint64(16)

    @property
    def message_number(self):
        return (self._words[1] & np.uint64(0x000000000000FF00)) >> np.uint64(8)

    @property
    def sub_cci_number(self):
        return self._words[1] & np.uint64(0x00000000000000FF)

    @property
    def crc(self) -> int:
        return int(self._words[2])

    @property
    def lane1_id(self) -> int:
        return (self._words[9] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def lane2_id(self) -> int:
        return (self._words[10] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def lane3_id(self) -> int:
        return (self._words[11] & np.uint64(
            0xFF00000000000000)) >> np.uint64(56)

    @property
    def path_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x00FF000000000000)) >> np.uint64(48)

    @property
    def path_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000FF0000000000)) >> np.uint64(40)

    @property
    def subpath_id(self) -> int:
        return (self._words[9] & np.uint64(
            0x000000F000000000)) >> np.uint64(36)

    @property
    def subpath_width(self) -> int:
        return (self._words[9] & np.uint64(
            0x0000000F00000000)) >> np.uint64(32)
