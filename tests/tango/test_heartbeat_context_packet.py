import pytest
import io
import struct

import numpy as np


import bip
from bip.plugins.tango.heartbeat_context_packet import _HeartbeatContextPacket as HeartbeatContextPacket


@pytest.fixture
def simple_heartbeat_packet(): #needs to be heavily changed
    header = 0x4CA10049 #header word
    packet_data = [
        header,

        0x576EA41D, # 1 stream id

        0x00000001, # 2 class id 0
        0x00010002, # 3 class id 1
        0x0000FFFF, # 4 tsi
        0xBE991A83, # 5 tsf0
        0x0000001C, # 6 tsf1

        #payload
        0x00000000, #7 tx_buffer_0
        0x00000000, #8 tx_buffer_1
        0x00000000, #9 tx_buffer_2
        0x00000000, #10 tx_buffer_3
        0x00000000, #11 tx_buffer_4
        0x00000000, #12 tx_buffer_5
        0x00000000, #13 tx_buffer_6
        0x00000000, #14 tx_buffer_7
        0x00000000, #15 tx_buffer_8
        0x00000000, #16 tx_buffer_9
        0x00000000, #17 tx_buffer_10
        0x00000000, #18 tx_buffer_11
        0x00000000, #19 tx_buffer_12
        0x00000000, #20 tx_buffer_13
        0x00000000, #21 tx_buffer_14
        0x00000000, #22 tx_buffer_15
        0x00000000, #23 rx_buffer_0 
        0x00000000, #24 rx_buffer_1
        0x00000000, #25 rx_buffer_2
        0x00000000, #26 rx_buffer_3
        0x00000000, #27 rx_buffer_4
        0x00000000, #28 rx_buffer_5
        0x00000000, #29 rx_buffer_6
        0x00000000, #30 rx_buffer_7
        0x00000000, #31 rx_buffer_8
        0x00000000, #32 rx_buffer_9
        0x00000000, #33 rx_buffer_10
        0x00000000, #34 rx_buffer_11
        0x00000000, #35 rx_buffer_12
        0x00000000, #36 rx_buffer_13
        0x00000000, #37 rx_buffer_14
        0x00000000, #38 rx_buffer_15
        0x00000000, #39 tx_stream_id_0
        0x00000000, #40 tx_stream_id_1
        0x00000000, #41 tx_stream_id_2
        0x00000000, #42 tx_stream_id_3
        0x00000000, #43 tx_stream_id_4
        0x00000000, #44 tx_stream_id_5
        0x00000000, #45 tx_stream_id_6
        0x00000000, #46 tx_stream_id_7
        0x00000000, #47 tx_stream_id_8
        0x00000000, #48 tx_stream_id_9
        0x00000000, #49 tx_stream_id_10
        0x00000000, #50 tx_stream_id_11
        0x00000000, #51 tx_stream_id_12
        0x00000000, #52 tx_stream_id_13
        0x00000000, #53 tx_stream_id_14
        0x00000000, #54 tx_stream_id_15
        0x00000000, #55 rx_stream_id_0
        0x00000000, #56 rx_stream_id_1
        0x00000000, #57 rx_stream_id_2
        0x00000000, #58 rx_stream_id_3
        0x00000000, #59 rx_stream_id_4
        0x00000000, #60 rx_stream_id_5
        0x00000000, #61 rx_stream_id_6
        0x00000000, #62 rx_stream_id_7
        0x00000000, #63 rx_stream_id_8
        0x00000000, #64 rx_stream_id_9
        0x00000000, #65 rx_stream_id_10
        0x00000000, #66 rx_stream_id_11
        0x00000000, #67 rx_stream_id_12
        0x00000000, #68 rx_stream_id_13
        0x00000000, #69 rx_stream_id_14
        0x00000000, #70 rx_stream_id_15
        0x00000000, #71 system_time 0
        0x00000000, #72 system_time 1
        ]

    with io.BytesIO() as f:
        for d in packet_data:
            f.write(struct.pack("<I", d))

        yield header, bytearray(f.getvalue())


def test_heartbeat_packet_create(simple_heartbeat_packet):
    _, payload = simple_heartbeat_packet
    packet = HeartbeatContextPacket(payload)
    assert packet is not None


def test_heartbeat_packet_header(simple_heartbeat_packet):
    header, payload = simple_heartbeat_packet

    packet = HeartbeatContextPacket(payload)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size ==  len(payload) // 4
    assert packet.packet_header.tsf == 0x2
    assert packet.packet_header.tsi == 0x2
    assert packet.packet_header.packet_type == 0x4
    assert packet.packet_header.class_id == True


def test_heartbeat_packet(simple_heartbeat_packet):
    packet = HeartbeatContextPacket(simple_heartbeat_packet[1])

    assert packet.stream_id == 0x576EA41D

    assert packet.integer_timestamp == 0xFFFF
    assert packet.fractional_timestamp[0]== 3197704835
    assert packet.fractional_timestamp[1] == 28
    assert packet.time == pytest.approx(65535.123456789123, 0.000001)

    #This will need to be updated when we know reasonable values for these variables
    assert packet.tx_buffer_free_0 == 0.0
    assert packet.tx_buffer_free_1 == 0.0
    assert packet.tx_buffer_free_2 == 0.0
    assert packet.tx_buffer_free_3 == 0.0
    assert packet.tx_buffer_free_4 == 0.0
    assert packet.tx_buffer_free_5 == 0.0
    assert packet.tx_buffer_free_6 == 0.0
    assert packet.tx_buffer_free_7 == 0.0
    assert packet.tx_buffer_free_8 == 0.0
    assert packet.tx_buffer_free_9 == 0.0
    assert packet.tx_buffer_free_10 == 0.0
    assert packet.tx_buffer_free_11 == 0.0
    assert packet.tx_buffer_free_12 == 0.0
    assert packet.tx_buffer_free_13 == 0.0
    assert packet.tx_buffer_free_14 == 0.0
    assert packet.tx_buffer_free_15 == 0.0
    
    assert packet.rx_buffer_free_0 == 0.0
    assert packet.rx_buffer_free_1 == 0.0
    assert packet.rx_buffer_free_2 == 0.0
    assert packet.rx_buffer_free_3 == 0.0
    assert packet.rx_buffer_free_4 == 0.0
    assert packet.rx_buffer_free_5 == 0.0
    assert packet.rx_buffer_free_6 == 0.0
    assert packet.rx_buffer_free_7 == 0.0
    assert packet.rx_buffer_free_8 == 0.0
    assert packet.rx_buffer_free_9 == 0.0
    assert packet.rx_buffer_free_10 == 0.0
    assert packet.rx_buffer_free_11 == 0.0
    assert packet.rx_buffer_free_12 == 0.0
    assert packet.rx_buffer_free_13 == 0.0
    assert packet.rx_buffer_free_14 == 0.0
    assert packet.rx_buffer_free_15 == 0.0

    assert packet.tx_stream_id_0 == 0.0
    assert packet.tx_stream_id_1 == 0.0
    assert packet.tx_stream_id_2 == 0.0
    assert packet.tx_stream_id_3 == 0.0
    assert packet.tx_stream_id_4 == 0.0
    assert packet.tx_stream_id_5 == 0.0
    assert packet.tx_stream_id_6 == 0.0
    assert packet.tx_stream_id_7 == 0.0
    assert packet.tx_stream_id_8 == 0.0
    assert packet.tx_stream_id_9 == 0.0
    assert packet.tx_stream_id_10 == 0.0
    assert packet.tx_stream_id_11 == 0.0
    assert packet.tx_stream_id_12 == 0.0
    assert packet.tx_stream_id_13 == 0.0
    assert packet.tx_stream_id_14 == 0.0
    assert packet.tx_stream_id_15 == 0.0

    assert packet.rx_stream_id_0 == 0.0
    assert packet.rx_stream_id_1 == 0.0
    assert packet.rx_stream_id_2 == 0.0
    assert packet.rx_stream_id_3 == 0.0
    assert packet.rx_stream_id_4 == 0.0
    assert packet.rx_stream_id_5 == 0.0
    assert packet.rx_stream_id_6 == 0.0
    assert packet.rx_stream_id_7 == 0.0
    assert packet.rx_stream_id_8 == 0.0
    assert packet.rx_stream_id_9 == 0.0
    assert packet.rx_stream_id_10 == 0.0
    assert packet.rx_stream_id_11 == 0.0
    assert packet.rx_stream_id_12 == 0.0
    assert packet.rx_stream_id_13 == 0.0
    assert packet.rx_stream_id_14 == 0.0
    assert packet.rx_stream_id_15 == 0.0
    
    assert packet.system_time == 0.0
