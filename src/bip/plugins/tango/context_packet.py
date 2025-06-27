from pathlib import Path

import pyarrow as pa
import numpy as np

from bip.vita import ContextPacket
from bip.common import bit_manipulation

# TODO: 64 bit values seem to be packed backwards instead of
#      [MSW, LSW] as called out in vita49.2 this looks like [LSW, MSW] at
#      least to make the number realistic
# TODO: related.  packing of two 16bits in a 32 needs sorted out.
#

# TODO: keep this up to date
##
# My reading of the spec / reverse engineering the one sample has this
# for the layout of the context packets
# This has been updated based on the information sent by Vendor.
##
# 0 header
# 1 stream id
# 2 class id 0
# 3 class id 1
# 4 tsi
# 5 tsf0
# 6 tsf1
# 7 cif0
# 8 cif1
# 9 cif2
# 10 cif3
##
# payload
# 11 bandwidth 0
# 12 bandwidth 1
# 13 IF ref freq 0
# 14 IF ref freq 1
# 15 RF ref freq
# 16 RF ref freq
# 17 gain 0/1
# 18 sample rate 0
# 19 sample rate 1
# 20 temperature
# 21 phase offset
# 22 elliticity / tilt
# 23   3d pointing
# 24   3d pointing (header_size(8), wrds/rec(12), num_records(12))
# 25   3d pointing ecef_0
# 26   3d pointing ecef_0
# 27   3d pointing ecef_1
# 28   3d pointing ecef_1
# 29   3d pointing ecef_2
# 30   3d pointing ecef_2
# 31   3d pointing elevation
# 32   3d pointing steering mode
# 33   3d pointing reserved
# 34   3d pointing reserved
# 35 beam width vert / beam width horiz
# 36 range
# 37 health
# 38 mode id
# 39 event id
# 40 pulse width 0
# 41 pulse width 1
# 42 PRI 0
# 43 PRI 1
# 44 duration 0
# 45 duration 1
# 46 Vita Frame align pad
# 47 Vita Frame align pad
# 48 Vita Frame align pad


_schema = [
    ("packet_id", pa.uint32(), None),

    ("packet_size", pa.uint16(), None),
    ("packet_count", pa.uint16(), None),
    ("tsfd", pa.uint8(), None),
    ("tsid", pa.uint8(), None),
    ("indicators", pa.uint8(), None),
    ("packet_type", pa.uint8(), None),

    ("tsi", pa.uint32(), None),
    ("tsf0", pa.uint32(), None),
    ("tsf1", pa.uint32(), None),
    ("time", pa.float64(), "GPS"),

    ("stream_id", pa.uint32(), None),
    ("classid0", pa.uint32(), None),
    ("classid1", pa.uint32(), None),
    ("classid_pad_bit_count", pa.uint8(), None),
    ("classid_oui", pa.uint32(), None),
    ("classid_information_class_code", pa.uint16(), None),
    ("classid_packet_class_code", pa.uint16(), None),

    ("cif0", pa.uint32(), None),
    ("cif1", pa.uint32(), None),
    ("cif2", pa.uint32(), None),
    ("cif3", pa.uint32(), None),

    ("bandwidth", pa.float64(), "MHz"),
    ("if_reference_freq", pa.float64(), "GHz"),
    ("rf_reference_freq", pa.float64(), "GHz"),

    ("gain1", pa.float32(), 'dB'),
    ("gain2", pa.float32(), 'dB'),

    ("sample_rate", pa.float64(), "MSps"),
    ("temperature", pa.float32(), "C"),
    ("phase_offset", pa.float32(), None),
    ("ellipticity", pa.float32(), None),
    ("tilt", pa.float32(), None),

    # 3d pointing structure

    ("array_size", pa.uint32(), None),
    ("num_records", pa.uint32(), None),
    ("num_words_per_rec", pa.uint32(), None),
    ("header_size", pa.uint32(), None),

    ("ecef_0", pa.float64(), "m"),
    ("ecef_1", pa.float64(), "m"),
    ("ecef_2", pa.float64(), "m"),

    ("azimuthal_angle_0", pa.float32(), "deg"),
    ("elevation_angle_0", pa.float32(), "deg"),

    ("steering_mode_0", pa.uint32(), None),
    ("reserved_0", pa.uint32(), None),
    ("reserved_1", pa.uint32(), None),

    ("beam_width_vert", pa.float32(), "deg"),
    ("beam_width_horiz", pa.float32(), "deg"),
    ("range", pa.float32(), "m"),
    ("health_status", pa.uint32(), None),
    ("mode_id", pa.uint32(), None),
    ("event_id", pa.uint32(), None),
    ("pulse_width", pa.float64(), "s"),
    ("pri", pa.float64(), "s"),
    ("duration", pa.float64(), "s"),

    ("frame_index", pa.uint32(), None),
    ("packet_index", pa.uint32(), None),

    ("local_context_key", pa.string(), None)
]


def _schema_elt(e: tuple) -> dict:
    return {
        "name": e[0],
        "type": str(e[1]),
        "unit": str(e[2]) if e[2] is not None else None
    }


schema = [_schema_elt(e) for e in _schema]


class _ContextPacket(ContextPacket):
    def __init__(self, payload: bytes, context_key: str = ""):
        super().__init__(payload)

        # right now we only handle 1 type of context packet
        assert self.class_id.information_class_code == 1
        assert self.class_id.packet_class_code == 2

        # make sure we have the right time codes
        assert self.packet_header.tsi == 0b10  # GPS time
        assert self.packet_header.tsf == 0b10  # real-time (ps) timestamp

        tsi = self.integer_timestamp
        tsf0, tsf1 = self.fractional_timestamp
        self.time = bit_manipulation.time(tsi, tsf0, tsf1)

        self.cif0 = self.words[7]
        self.cif1 = self.words[8]
        self.cif2 = self.words[9]
        self.cif3 = self.words[10]

        # currently these values are hardcoded, we want this to break loudly
        # if/when this changes
        #
        # TODO: this disagrees with the spec which has
        #       cif0: 00111000 10100100 00010000 00001110
        assert self.cif0 == 0b00111000101001000000000000001110
        assert self.cif1 == 0b11010011000000000000000000010000
        assert self.cif2 == 0b00000000000000000000000110000000
        assert self.cif3 == 0b00000001110000000000000000000000

        '''
        Rule 9.5.1-2 VITA 49.2 SPEC
        The Bandwidth field
        shall use the 64-bit, two’s-complement format shown in Figure 9.5.1-1. This field has an integer and a
        fractional part with the radix point to the right of bit 20 in the second 32-bit word.
        range: 0.00 to 8.79 terahertz
        resolution: 0.95 microhertz
        '''
        self.bandwidth = int(self.words[11:13].view(
            dtype=np.int64)[0]) * (2**-20) * (1e-6)

        '''
        Rule 9.5.5-3 VITA 49.2 SPEC
        The IF Reference Frequency subfield shall use the 64-bit, two’s-complement format as shown in Figure 9.5.5-1.
        This field has an integer and a fractional part, with the radix point to the right of bit 20 in the second
        32-bit word.
        range: +- 8.79 terahertz
        resolution: 0.95 microhertz
        '''
        self.if_reference_freq = int(self.words[13:15].view(
            dtype=np.int64)[0]) * (2**-20) * (1e-9)

        '''
        Rule 9.5.10-2 VITA 49.2 2017 SPEC
        This subfield has an integer and a fractional part, with the radix point to the right of bit 20 in the
        second 32-bit word.
        '''
        self.rf_reference_freq = int(self.words[15:17].view(
            dtype=np.int64)[0]) * (2**-20) * (1e-9)

        '''
        Rule 9.5.3-3
        The values of the Gain subfields have a range of near r256 dB with a resolution of 1/128 dB (0.0078125 dB).
        range: [-256, 256] dB
        resolution: 0.0078125 dB
        '''
        self.gain1, self.gain2 = self.words[17:18].view(dtype=np.int16)
        self.gain1 = self.gain1 * (2**-7)
        self.gain2 = self.gain2 * (2**-7)

        '''
        Rule 9.5.12-2
        This field has an integer and a fractional part, with the radix point to the right of bit 20 in the second
        32-bit word.
        range: [0.00, 8.79 terahertz]
        resolution: 0.95 micro-hertz
        '''
        self.sample_rate = int(self.words[18:20].view(
            dtype=np.int64)[0]) * (2**-20) * (1e-6)

        '''
        Rule 9.10.5-1
        The Temperature value shall be expressed in two's-complement
        format in the lower 16 bits of this field. This field has an integer and a fractional part, with the
        radix point to the right of bit 6.
        range: -273.15 C to 511.984375 C.
        resolution: 0.015625 C (1/64 C) (Obesrvation 9.10.5-1)
        '''
        self.temperature = int(
            self.words[20:21].view(dtype=np.int16)[0]) * (2**-6)

        '''
        Rule 9.5.8-2 Vita 49.2 SPEC
        This field has an integer and a fractional part, with the radix point to the right of bit 7 of the field.
        '''
        self.phase_offset = int(
            self.words[21:22].view(dtype=np.int16)[0]) * (2**-7)

        '''
        Rule 9.4.8-2 VITA 49.2 SPEC
        the Ellipticity
        Angle value expressed in two's-complement format in the lower 16 bits of the Polarization field. This
        subfield has an integer and a fractional part, with the radix point to the right of bit 7 of the subfield.
        '''
        ellipticity, tilt = self.words[22:23].view(dtype=np.int16)
        self.ellipticity = int(ellipticity) * (2**-13)

        '''
        Rule 9.4.8-3 VITA 49.2 SPEC
        Tilt Angle value expressed in two's-complement format in the upper 16 bits of the Polarization field. This
        subfield has an integer and a fractional part, with the radix point to the right of bit 7 of the subfield.
        '''
        self.tilt = int(tilt) * (2**-13)

        # 3d Pointing Vector Structure
        self.array_size = self.words[23]
        self.header_size = int(f"{self.words[24]:032b}"[:8], 2)
        self.num_words_per_rec = int(f"{self.words[24]:032b}"[8:20], 2)
        self.num_records = int(f"{self.words[24]:032b}"[20:], 2)

        self.ecef_0 = self.words[25:27].view(dtype=np.float64)
        self.ecef_1 = self.words[27:29].view(dtype=np.float64)
        self.ecef_2 = self.words[29:31].view(dtype=np.float64)

        '''
        Rule 9.4.1.1-2
        range: 0 to 511.9921875 degrees
        resolution: 0.0078125 degrees

        This rule is not true for this data
        '''
        azimuthal_angle_0, elevation_angle_0 = self.words[31:32].view(
            dtype=np.int16)
        self.azimuthal_angle_0 = azimuthal_angle_0 * (2**-7)

        '''
        Rule 9.4.1.1-3
        range: -90 to 90 degrees
        resolution: 0.0078125 degrees
        '''
        self.elevation_angle_0 = elevation_angle_0 * (2**-7)
        self.steering_mode_0 = self.words[32]
        self.reserved_0 = self.words[33]
        self.reserved_1 = self.words[34]

        '''
        VITA 49.2 spec says "this field has an integer and a fractional part, with the
        radix point to the right of bit 7 of the field." Does this mean this value should be a float??

        range: 0 to 360 degrees
        '''
        self.beam_width_vert = int(self.words[35] >> 16) * (2**-7)
        self.beam_width_horiz = int(self.words[35] & 0xFFFF) * (2**-7)

        '''
        Rule 9.4.10-1 VITA 49.2 SPEC
        Range has a fractional resolution of 0.015625m (1.56cm).
        range: 0 to 67,108,864m
        '''
        self.range = int(self.words[36]) * (2**-6)

        '''
        Rule 9.10.2-1
        The Health Status shall use the lower 16 bits of a 32 bit word
        '''
        self.health_status = int(self.words[37])
        self.mode_id = int(self.words[38])
        self.event_id = int(self.words[39])

        '''
        Rule 9.7-1
        "The most significant 32 bits shall be in the first of these two words. The lsb of each word shall be
        on the right."
        LSB is 1 femtosecond (Rule 9.7-2)
        type: fractional time
        range: +- 9223 seconds (Observation 9.7-5)
        '''
        self.pulse_width = int(
            self.words[40:42].view(dtype=np.int64)[0]) * (1e-15)
        self.pri = int(self.words[42:44].view(dtype=np.int64)[0]) * (1e-15)
        self.duration = int(self.words[44:46].view(
            dtype=np.int64)[0]) * (1e-15)

        if ("{stream_id}" in context_key):
            self.context_packet_key = context_key.format(
                stream_id=self.stream_id)
        else:
            self.context_packet_key = context_key


class Context:
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
                   packet: _ContextPacket,
                   *,
                   frame_index: int,
                   packet_index: int):
        assert isinstance(packet, _ContextPacket)
        header = packet.packet_header

        self.recorder.add_record({
            "packet_id": np.uint32(self.packet_id),

            "packet_size": np.uint16(header.packet_size + 1),
            "packet_count": np.uint16(header.packet_count),
            "tsfd": np.uint8(header.tsf),
            "tsid": np.uint8(header.tsi),
            "indicators": np.uint8(header.indicators),
            "packet_type": np.uint8(header.packet_type),

            "tsi": np.uint32(packet.integer_timestamp),
            "tsf0": np.uint32(packet.fractional_timestamp[0]),
            "tsf1": np.uint32(packet.fractional_timestamp[1]),
            "time": np.float64(packet.time),

            "stream_id": np.uint32(packet.stream_id),
            "classid0": np.uint32(packet.class_id._data[0]),
            "classid1": np.uint32(packet.class_id._data[1]),
            "classid_pad_bit_count": np.uint8(packet.class_id.pad_bit_count),
            "classid_oui": np.uint32(packet.class_id.oui),
            "classid_information_class_code": np.uint16(packet.class_id.information_class_code),
            "classid_packet_class_code": np.uint16(packet.class_id.packet_class_code),

            "cif0": np.uint32(packet.cif0),
            "cif1": np.uint32(packet.cif1),
            "cif2": np.uint32(packet.cif2),
            "cif3": np.uint32(packet.cif3),

            "bandwidth": np.float64(packet.bandwidth),
            "if_reference_freq": np.float64(packet.if_reference_freq),
            "rf_reference_freq": np.float64(packet.rf_reference_freq),

            "gain1": np.float32(packet.gain1),
            "gain2": np.float32(packet.gain2),

            "sample_rate": np.float64(packet.sample_rate),
            "temperature": np.float32(packet.temperature),
            "phase_offset": np.float32(packet.phase_offset),
            "ellipticity": np.float32(packet.ellipticity),
            "tilt": np.float32(packet.tilt),

            "array_size": np.uint32(packet.array_size),
            "num_records": np.uint32(packet.num_records),
            "num_words_per_rec": np.uint32(packet.num_words_per_rec),
            "header_size": np.uint32(packet.header_size),

            "ecef_0": np.float64(packet.ecef_0),
            "ecef_1": np.float64(packet.ecef_1),
            "ecef_2": np.float64(packet.ecef_2),

            "azimuthal_angle_0": np.float32(packet.azimuthal_angle_0),
            "elevation_angle_0": np.float32(packet.elevation_angle_0),

            "steering_mode_0": np.uint32(packet.steering_mode_0),
            "reserved_0": np.uint32(packet.reserved_0),
            "reserved_1": np.uint32(packet.reserved_0),

            "beam_width_vert": np.float32(packet.beam_width_vert),
            "beam_width_horiz": np.float32(packet.beam_width_horiz),
            "range": np.float32(packet.range),
            "health_status": np.uint32(packet.health_status),
            "mode_id": np.uint32(packet.mode_id),
            "event_id": np.uint32(packet.event_id),
            "pulse_width": np.float64(packet.pulse_width),
            "pri": np.float64(packet.pri),
            "duration": np.float64(packet.duration),

            "frame_index": np.uint32(frame_index),
            "packet_index": np.uint32(frame_index),

            "local_context_key": packet.context_packet_key
        })

    def process(self,
                payload: bytes,
                *,
                frame_index: int,
                packet_index: int,
                context_packet_key: str = ""):
        self.add_record(_ContextPacket(payload, context_packet_key),
                        frame_index=frame_index,
                        packet_index=packet_index)
        self.packet_id += 1

    @property
    def metadata(self) -> dict:
        return self.recorder.metadata | {"schema": schema}
