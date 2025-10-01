import pytest
import io
import struct
import logging

from pathlib import Path

from bip.plugins.tango.frame import unpack_header
from bip.plugins.tango.parser import Parser
from bip.recorder.dummy.dummywriter import DummyWriter
from bip.recorder.parquet.pqwriter import PQWriter


@pytest.fixture
def fake_file():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<IIIIII", (0x1 << 20) | 8 , 1, 2, 3, 4, 5))
    f.write(bytes("DNEV", encoding="ascii"))
    f.seek(0)
    yield f


def test_read_packet(fake_file):
    def add_record(rec: dict):
        global called
        assert rec["frame_count"] == 1
        assert rec["frame_size"] == 8

    parser =  Parser(Path(), Path(), DummyWriter, logging.WARNING,
            recorder_opts={ 'add_record_callback': add_record }
            )
    payload, payload_size = parser.read_packet(fake_file)
    expected_payload = struct.pack("<IIIII", 1, 2, 3, 4, 5)
    assert payload == expected_payload
    assert payload_size == (len(expected_payload) / 4)


def test_bad_header_no_vrlp():
    with io.BytesIO() as f:
        f.write(bytes("XYZW", encoding="ascii"))
        f.write(struct.pack("<IIIIII", (0x1 << 20) | 8 , 1, 2, 3, 4, 5))
        f.write(bytes("DNEV", encoding="ascii"))
        f.seek(0)

        parser = Parser(Path(), Path(), DummyWriter, logging.WARNING)
        with pytest.raises(RuntimeError):
            parser.read_packet(f)


def test_bad_header_no_vend():
    with io.BytesIO() as f:
        f.write(bytes("PLRV", encoding="ascii"))
        f.write(struct.pack("<IIIIII", (0x1 << 20) | 8 , 1, 2, 3, 4, 5))
        f.write(bytes("XYZW", encoding="ascii"))
        f.seek(0)

        parser = Parser(Path(), Path(), DummyWriter, logging.WARNING)
        payload, _ = parser.read_packet(f)

        assert payload == "BAD_PACKET"

def test_bad_header_short():
    with io.BytesIO() as f:
        f.write(bytes("PLRV", encoding="ascii"))
        f.seek(0)

        parser = Parser(Path(), Path(), DummyWriter, logging.WARNING)
        with pytest.raises(RuntimeError):
            parser.read_packet(f)

def test_read_custom_packet_empty():
    parser = Parser(Path(), Path(), DummyWriter, logging.WARNING)
    payload, payload_size = parser.read_packet(io.BytesIO())
    assert payload is None
    assert payload_size is None


def test_bad_packet_containing_deadbeef_clean():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<II", (0x1 << 20) | 8 , 1))
    f.write(struct.pack("<IIII", 0xDEADBEEF, 0XDEADBEEF, 0xDEADBEEF, 0XDEADBEEF))
    f.write(struct.pack("<IIII", 2, 3, 4, 5))
    f.write(struct.pack("<IIII", 0xDEADBEEF, 0XDEADBEEF, 0xDEADBEEF, 0XDEADBEEF))
    f.write(bytes("DNEV", encoding="ascii"))
    f.seek(0)

    parser =  Parser(Path(), Path(), DummyWriter, logging.WARNING, clean = True)
    payload, payload_size = parser.read_packet(f)

    expected_payload = struct.pack("<IIIII", 1, 2, 3, 4, 5)
    assert payload == expected_payload
    assert payload_size == (len(expected_payload) / 4)

def test_bad_packet_containing_multiple_deadbeef_clean():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<II", (0x1 << 20) | 8 , 1))
    f.write(struct.pack("<IIII", 0xDEADBEEF, 0XDEADBEEF, 0xDEADBEEF, 0XDEADBEEF))
    f.write(struct.pack("<II", 2, 3))
    f.write(struct.pack("<IIII", 0xDEADBEEF, 0XDEADBEEF, 0xDEADBEEF, 0XDEADBEEF))
    f.write(struct.pack("<II", 4, 5))
    f.write(bytes("DNEV", encoding="ascii"))
    f.seek(0)

    parser =  Parser(Path(), Path(), DummyWriter, logging.WARNING, clean = True)
    payload, payload_size = parser.read_packet(f)

    expected_payload = struct.pack("<IIIII", 1, 2, 3, 4, 5)
    assert payload == expected_payload
    assert payload_size == (len(expected_payload) / 4)

def test_bad_packet_containing_deadbeef_noclean():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<IIIIII", (0x1 << 20) | 8 , 1, 2, 3, 4, 5))
    f.write(bytes("EFBEADDEEFBEADDEEFBEADDEEFBEADDE", encoding="ascii"))
    f.write(bytes("DNEV", encoding="ascii"))
    f.seek(0)

    parser =  Parser(Path(), Path(), DummyWriter, logging.WARNING)
    payload, payload_size = parser.read_packet(f)

    assert payload == 'BAD_PACKET'
    assert payload_size is None

def process_packet_unhandled_packet_type():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<IIIIII", (0x1 << 20) | 8 , 1, 2, 3, 4, 5))
    f.write(bytes("DNEV", encoding="ascii"))
    packet_type = 11
    class_id = 65537

    parser =  Parser(Path(), Path(), DummyWriter, logging.WARNING)

    # When the packet_type is unhandled process_packet
    # will attempt to access self. variables that are not
    # initialized here throwing a runtime error
    with pytest.raises(RuntimeError):
        parser.process_packet(packet_type, class_id, f)


def test_bad_packet_size_smaller_than_stated():
    f = io.BytesIO()
    f.write(bytes("PLRV", encoding="ascii"))
    f.write(struct.pack("<IIIIII", (0x1 << 20) | 9 , 1, 2, 3, 4, 5))
    f.write(bytes("DNEV", encoding="ascii"))
    f.write(bytes("PLRV", encoding="ascii"))
    f.seek(0)

    parser = Parser(Path(), Path(), DummyWriter, logging.WARNING)
    payload, payload_size = parser.read_packet(f)

    assert payload == 'BAD_PACKET'
    assert payload_size is None
