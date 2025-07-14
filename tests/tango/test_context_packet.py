import pytest
import io
import struct

import numpy as np


import bip
from bip.plugins.tango.context_packet import _ContextPacket as ContextPacket


@pytest.fixture
def simple_cp_packet():
    header = 0x4CA10031 #header word
    packet_data = [
        header,
        0x576EA41D, # 1 stream id
        0x00000001, # 2 class id 0
        0x00010002, # 3 class id 1
        0x0000FFFF, # 4 tsi
        0xBE991A83, # 5 tsf0
        0x0000001C, # 6 tsf1
        0b00111000101001000000000000001110, # 7 cif0
        0b11010011000000000000000000010000, # 8 cif1
        0b00000000000000000000000110000000, # 9 cif2
        0b00000001110000000000000000000000, #10 cif3

        #payload
        0x00000001, #11 bandwidth 0
        0x00000000, #12 bandwidth 1
        0x00000001, #13 IF ref freq 0
        0x00000000, #14 IF ref freq 1

        0x80000000, #15 RF ref freq
        0x00100000, #16 RF ref freq
        0x00010001, #17 gain 0/1
        0x80000000, #18 sample rate 0
        0x00001000, #19 sample rate 1
        0x00000001, #20 temperature
        0x00000000, #21 phase offset
        0x15000000, #22 elliticity / tilt
        0x00000000, #23   3d pointing
        0x00000000, #24   3d pointing (header_size(8), wrds/rec(12), num_records(12))
        0x00000000, #25   3d pointing ecef_0
        0x00000000, #26   3d pointing ecef_0
        0x00000000, #27   3d pointing ecef_1
        0x00000000, #28   3d pointing ecef_1
        0x00000000, #29   3d pointing ecef_2
        0x00000000, #30   3d pointing ecef_2

        0x00010001, #31   3d pointing elevation
        0x00000001, #32   3d pointing steering mode

        0x00000000, #33   3d pointing reserved
        0x00000000, #34   3d pointing reserved
        0x00000000, #35 beam width vert / beam width horiz
        0x11000000, #36 range
        0x00007777, #37 health
        0xABCDEFAB, #38 mode id
        0x01020304, #39 event id
        0x50000000, #40 pulse width 0
        0x0000a000, #41 pulse width 1

        0x00000001, #42 PRI 0
        0x00000000, #43 PRI 1
        0x00000001, #44 duration 0
        0x00000000, #45 duration 1
        0x00000000, #46 Vita Frame align pad
        0x00000000, #46 Vita Frame align pad
        0x00000000, #46 Vita Frame align pad
        ]

    with io.BytesIO() as f:
        for d in packet_data:
            # < means little endian, I means unsigned integer
            # the byte array has the bytes in little endian
            f.write(struct.pack("<I", d))

        yield header, bytearray(f.getvalue())


def test_cp_packet_create(simple_cp_packet):
    _, payload = simple_cp_packet
    packet = ContextPacket(payload)
    assert packet is not None


def test_cp_packet_header(simple_cp_packet):
    header, payload = simple_cp_packet

    packet = ContextPacket(payload)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size ==  len(payload) // 4
    assert packet.packet_header.tsf == 0x2
    assert packet.packet_header.tsi == 0x2
    assert packet.packet_header.packet_type == 0x4
    assert packet.packet_header.class_id == True


def test_cp_packet(simple_cp_packet):
    packet = ContextPacket(simple_cp_packet[1])

    assert packet.stream_id == 0x576EA41D

    assert packet.integer_timestamp == 0xFFFF

    assert packet.fractional_timestamp[0]== 3197704835
    assert packet.fractional_timestamp[1] == 28
    assert packet.time == pytest.approx(65535.123456789123, 0.000001)
    
    assert packet.bandwidth == pytest.approx((0.95 * 1e-12), 0.001)
    assert packet.if_reference_freq == pytest.approx((0.95 * 1e-12), 0.001)

    assert packet.rf_reference_freq == pytest.approx(4.295, 0.001)
    assert packet.gain1 == pytest.approx(0.0078125, 0.001)
    assert packet.gain2 == pytest.approx(0.0078125, 0.001)
    assert packet.sample_rate == pytest.approx(16.779, 0.001)
    assert packet.temperature == pytest.approx(0.015625, 0.001)
    assert np.isclose(packet.phase_offset, 0.0, rtol=1e-09, atol=1e-09)
    assert packet.ellipticity == pytest.approx(0.0, 0.001)
    assert packet.tilt == pytest.approx(0.656, 0.001)
    
    assert packet.azimuthal_angle_0 == pytest.approx(0.0078125, 0.001)
    assert packet.elevation_angle_0 == pytest.approx(0.0078125, 0.001)
    assert packet.steering_mode_0 == pytest.approx(1, 0.001)
    
    assert np.isclose(packet.beam_width_vert, 0.0, rtol=1e-09, atol=1e-09)
    assert np.isclose(packet.beam_width_horiz, 0.0, rtol=1e-09, atol=1e-09)
    assert packet.range == pytest.approx(4456448.0, 1.0)  

    assert packet.health_status == 0x00007777
    assert packet.mode_id == 0xABCDEFAB
    assert packet.event_id == 0x01020304
    assert np.isclose(packet.pulse_width,
                      0.175923202621440,
                      rtol=1e-09, atol=1e-09)

    assert packet.pri == pytest.approx(1e-15, 0.001)
    assert packet.duration == pytest.approx(1e-15, 0.001)
