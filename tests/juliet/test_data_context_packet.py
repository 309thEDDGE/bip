import pytest
import io
import struct

import numpy as np

import bip
from bip.plugins.juliet.data_context_packet import _DataContextPacket as dcp

@pytest.fixture
def simple_dcp_packet():
    header = 0x58E10022 #header word
    packet_data = [
        header,
        0xB1DED1ED, # 1 stream id
        0x00000001, # 2 class id 0
        0xF0000000, # 3 class id 1
        0x0000FFFF, # 4 tsi
        0x00000000, # 5 tsf0
        0x10000000, # 6 tsf1
        0x8C20801E, # 7 cif0
        0x20000000, # 8 cif1
        0x00000000, # 9 cif2
        0x00200000, #10 cif3
        0x01000000, #11 cif4
        0x00000000, #12 bandwidth0
        0x00000000, #13 bandwidth1
        0xFFFFFFFF, #14 rf_ref_freq0
        0xFFF00000, #15 rf_ref_freq1
        0x00AE0000, #16 rf_freq_offset0
        0x09650000, #17 rf_freq_offset1
        0x00000005, #18 gain
        0x00009896, #19 sample_rate0
        0x80000000, #20 sample_rate1
        0x200003CF, #21 data_format0
        0x00000000, #22 data_format1
        0x00000000, #23 polarization
        0x010A020B, #24 pointing3d
        0x00000000, #25 beamWidth 
        0x00000003, #26 citedSID
        0x0000000A, #27 func_priority_id
        0x00001234, #28 dwell0
        0xFEDC0000, #29 dwell1
        0x80000000, #30 requested_input_GT 
        0x0000000E, #31 reject_reason 
        0x00000010, #32 data_addr_index 
        0x00000100  #33 TxDigitalInputPower 
        ]

    with io.BytesIO() as f:
        for d in packet_data:
            # "<I" is '<' big endian 'I' is unsigned integer
            f.write(struct.pack("<I", d))

        yield header, bytearray(f.getvalue())


def test_data_context_packet_create(simple_dcp_packet):
    header, payload = simple_dcp_packet
    packet = dcp(payload)
    assert packet is not None


def test_data_context_packet_header(simple_dcp_packet):
    header, payload = simple_dcp_packet

    packet = dcp(payload)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size ==  len(payload) // 4
    assert packet.packet_header.tsf == 0x2
    assert packet.packet_header.tsi == 0x3
    assert packet.packet_header.packet_type == 0b0101
    assert packet.packet_header.indicators == 0b0000
    assert packet.packet_header.class_id == True


def test_dcp_packet(simple_dcp_packet):
    packet = dcp(simple_dcp_packet[1])

    assert packet.stream_id == 0xB1DED1ED
    classId0, classId1 = packet.class_identifier
    assert classId0 == 1
    assert classId1 == 0xF0000000
    assert packet.integer_timestamp == 0xFFFF
    assert packet.fractional_timestamp[0]== 0
    assert packet.fractional_timestamp[1] == 0x10000000
    assert packet.sampling_rate == 160
    assert packet.dwell == 20018823430144 * 10 **-9#((0x00001234 << 32) + 0xFEDC0000) * 10**-9
    assert packet.freq == 17592.186044415
    assert packet.rfFreqOffset == 46707769494.3125 * (10**-9)
    assert packet.beamWidth == 0
    assert packet.gain == 0x5
    assert packet.dataFormat0 == 0x200003CF
    assert packet.dataFormat1 == 0
    assert packet.polarization == 0
    assert packet.azimuth == 4.0859375
    assert packet.elevation == 2.078125
    assert packet.functionPriorityId == 0xA
    assert packet.data_addr_index == 0x10
    assert packet.TxDigitalInputPower == 0x100

@pytest.fixture
def simple_dcp_packet_II():
    header = 0x401C0022 #header word
    packet_data = [
        header,
        0xC42A1760, # 1 stream id
        0x00000000, # 2 class id 0
        0x00000000, # 3 class id 1        
        0x00000000, # 4 tsi
        0x00000000, # 5 tsf0
        0x10000000, # 6 tsf1
        0x8C20801E, # 7 cif0
        0x20000000, # 8 cif1
        0x00000000, # 9 cif2
        0x00200000, #10 cif3
        0x01000000, #11 cif4
        0x00000000, #12 bandwidth0
        0x00000000, #13 bandwidth1
        0xFFFFFFFF, #14 rf_ref_freq0
        0xFFFFFFFF, #15 rf_ref_freq1
        0x00AE0000, #16 rf_freq_offset0
        0x09650000, #17 rf_freq_offset1
        0x00000003, #18 gain
        0x00009896, #19 sample_rate0
        0x80000000, #20 sample_rate1
        0x200003CF, #21 data_format0
        0x00000000, #22 data_format1
        0x00000000, #23 polarization
        0x010A020B, #24 pointing3d
        0x00000000, #25 beamWidth 
        0x00000003, #26 citedSID
        0x0000000A, #27 func_priority_id
        0x000003A3, #28 dwell0
        0x52944000, #29 dwell1
        0x80000000, #30 requested_input_GT 
        0x0000000E, #31 reject_reason 
        0x00000010, #32 data_addr_index 
        0x00000100  #33 TxDigitalInputPower 
        ]
    
    with io.BytesIO() as f:
        for d in packet_data:
            f.write(struct.pack("<I", d))

        yield header, bytearray(f.getvalue())

def test_data_context_packet_header_II(simple_dcp_packet_II):
    header, payload = simple_dcp_packet_II

    packet = dcp(payload)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size ==  len(payload) // 4
    assert packet.packet_header.tsf == 0x1
    assert packet.packet_header.tsi == 0x0
    assert packet.packet_header.packet_type == 0b0100
    assert packet.packet_header.indicators == 0b0000
    assert packet.packet_header.class_id == False

def test_dcp_packet_II(simple_dcp_packet_II):
    packet = dcp(simple_dcp_packet_II[1])

    assert packet.stream_id == 0xC42A1760

    assert packet.integer_timestamp == 0x0000
    assert packet.fractional_timestamp[0]== 0
    assert packet.fractional_timestamp[1] == 0x10000000
    assert packet.sampling_rate == 160
    assert int(packet.dwell) == 4000 # easier to round it off
    assert packet.freq == 17592.186044416
    assert packet.rfFreqOffset == 46707769494.3125 * (10**-9)
    assert packet.beamWidth == 0
    assert packet.gain == 0x3
    assert packet.dataFormat0 == 0x200003CF
    assert packet.dataFormat1 == 0
    assert packet.polarization == 0
    assert packet.azimuth == 4.0859375
    assert packet.elevation == 2.078125
    assert packet.functionPriorityId == 0xA
    assert packet.data_addr_index == 0x10
    assert packet.TxDigitalInputPower == 0x100

