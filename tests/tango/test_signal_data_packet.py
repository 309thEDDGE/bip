import io
import struct

import numpy as np
import pytest

import bip
from bip.plugins.tango.signal_data_packet import _SignalDataPacket as DataPacket

@pytest.fixture
def simple_data_packet():
    with io.BytesIO() as f:
        header = 0x1CE10009 #header word
        f.write(struct.pack("<I", header))
        f.write(struct.pack("<I", 0x576EA41D)) #stream id
        f.write(struct.pack("<I", 0x00000001)) #class id 0
        f.write(struct.pack("<I", 0xF0000000)) #class id 1
        f.write(struct.pack("<I", 0x0000FFFF)) #tsi
        f.write(struct.pack("<I", 0x00000000)) #tsf0
        f.write(struct.pack("<I", 0x10000000)) #tsf1
        f.write(struct.pack("<I", 0x0A0B0C0D)) #data
        f.write(struct.pack("<I", 0xAAAAAAAA)) #trailer 0
        f.write(struct.pack("<I", 0xFFFFFFFF)) #trailer 1
        yield header, bytearray(f.getvalue())

def test_data_packet_create(simple_data_packet):
    header, payload = simple_data_packet
    payload_size_words = 7
    
    packet = DataPacket(payload, payload_size_words)
    assert packet is not None


def test_data_packet_header(simple_data_packet):
    header, payload = simple_data_packet
    payload_size_words = 7
    
    packet = DataPacket(payload, payload_size_words)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size == 9
    assert packet.packet_header.packet_count == 1
    assert packet.packet_header.tsf == 0x2
    assert packet.packet_header.tsi == 0x3
    assert packet.packet_header.packet_type == 0x1
    assert packet.packet_header.class_id == True

    assert packet.signal_data_indicators.trailer == True
    assert packet.signal_data_indicators.not_vita_49_0 == False
    assert packet.signal_data_indicators.signal_spectrum == False


def test_data_packet(simple_data_packet):
    packet = DataPacket(simple_data_packet[1], 7)
    assert packet.stream_id == 0x576EA41D
    assert packet.integer_timestamp == 0xFFFF
    assert packet.fractional_timestamp[0] == 0
    assert packet.fractional_timestamp[1] == 0x10000000
    assert packet.trailer[0] == 0xAAAAAAAA
    assert packet.trailer[1] == 0xFFFFFFFF
    assert packet.time == 65535.000268435455


def test_data_packet_data(simple_data_packet):
    packet = DataPacket(simple_data_packet[1], 7)
    assert np.array_equal(
            packet.data[0],
            np.array([0x0c0d, 0x0a0b], dtype = np.int16))


@pytest.fixture
def data_packet_multiple():
    with io.BytesIO() as f:
        header = 0x1CE1000B #header word
        f.write(struct.pack("<I", header))
        f.write(struct.pack("<I", 0x576EA41D)) #stream id
        f.write(struct.pack("<I", 0x00000001)) #class id 0
        f.write(struct.pack("<I", 0xF0000000)) #class id 1
        f.write(struct.pack("<I", 0x0000FFFF)) #tsi
        f.write(struct.pack("<I", 0x00000000)) #tsf0
        f.write(struct.pack("<I", 0x10000000)) #tsf1
        f.write(struct.pack("<I", 0x0A0B0C0D)) #data
        f.write(struct.pack("<I", 0xA0B0C0D0)) #data
        f.write(struct.pack("<I", 0xCCDDAABB)) #data
        f.write(struct.pack("<I", 0xAAAAAAAA)) #trailer 0
        f.write(struct.pack("<I", 0xFFFFFFFF)) #trailer 1
        yield header, bytearray(f.getvalue())


def test_data_packet_multiple_data(data_packet_multiple):
    packet = DataPacket(data_packet_multiple[1], 12)
    assert np.array_equal(
            packet.data,
            np.array([
                [0x0c0d, 0x0a0b],
                [0xc0d0, 0xa0b0],
                [0xaabb, 0xccdd]], dtype = np.uint16).astype(np.int16))


@pytest.fixture
def data_packet_notrailer():
    with io.BytesIO() as f:
        header = 0x18E10008 #header word
        f.write(struct.pack("<I", header))
        f.write(struct.pack("<I", 0x576EA41D)) #stream id
        f.write(struct.pack("<I", 0x00000001)) #class id 0
        f.write(struct.pack("<I", 0xF0000000)) #class id 1
        f.write(struct.pack("<I", 0x0000FFFF)) #tsi
        f.write(struct.pack("<I", 0x00000000)) #tsf0
        f.write(struct.pack("<I", 0x10000000)) #tsf1
        f.write(struct.pack("<I", 0x0A0B0C0D)) #data
        yield header, bytearray(f.getvalue())


def test_data_packet_notrailer(data_packet_notrailer):
    packet = DataPacket(data_packet_notrailer[1], 6)
    assert packet.signal_data_indicators.trailer == False


@pytest.fixture
def simple_data_packet_wrong_size():
    with io.BytesIO() as f:
        header = 0x1CE1000B #header word
        f.write(struct.pack("<I", header))
        f.write(struct.pack("<I", 0x576EA41D)) #stream id
        f.write(struct.pack("<I", 0x00000001)) #class id 0
        f.write(struct.pack("<I", 0xF0000000)) #class id 1
        f.write(struct.pack("<I", 0x0000FFFF)) #tsi
        f.write(struct.pack("<I", 0x00000000)) #tsf0
        f.write(struct.pack("<I", 0x10000000)) #tsf1
        f.write(struct.pack("<I", 0x0A0B0C0D)) #data
        f.write(struct.pack("<I", 0xAAAAAAAA)) #trailer 0
        f.write(struct.pack("<I", 0xFFFFFFFF)) #trailer 1
        yield header, bytearray(f.getvalue())

def test_data_packet_wrong_size_create(simple_data_packet_wrong_size):
    header, payload = simple_data_packet_wrong_size
    payload_size_words = 7
    
    packet = DataPacket(payload, payload_size_words)
    assert packet is not None


def test_data_packet_wrong_size_header(simple_data_packet_wrong_size):
    header, payload = simple_data_packet_wrong_size
    payload_size_words = 7
    
    packet = DataPacket(payload, payload_size_words)
    assert packet.packet_header.value == header
    assert packet.packet_header.packet_size == 11
    assert packet.packet_header.packet_count == 1
    assert packet.packet_header.tsf == 0x2
    assert packet.packet_header.tsi == 0x3
    assert packet.packet_header.packet_type == 0x1
    assert packet.packet_header.class_id == True

    assert packet.signal_data_indicators.trailer == True
    assert packet.signal_data_indicators.not_vita_49_0 == False
    assert packet.signal_data_indicators.signal_spectrum == False


def test_data_packet_wrong_size(simple_data_packet_wrong_size):
    packet = DataPacket(simple_data_packet_wrong_size[1], 7)
    assert packet.stream_id == 0x576EA41D
    assert packet.integer_timestamp == 0xFFFF
    assert packet.fractional_timestamp[0] == 0
    assert packet.fractional_timestamp[1] == 0x10000000
    assert packet.trailer[0] == 0xAAAAAAAA
    assert packet.trailer[1] == 0xFFFFFFFF
    assert packet.time == 65535.000268435455

def test_data_packet_wrong_size_data(simple_data_packet_wrong_size):
    packet = DataPacket(simple_data_packet_wrong_size[1], 7)
    assert np.array_equal(
            packet.data[0],
            np.array([0x0c0d, 0x0a0b], dtype = np.int16))