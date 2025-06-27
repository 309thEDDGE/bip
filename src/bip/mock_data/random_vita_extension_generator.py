import struct
import random
import uuid


def add_packet_header(bin_file):
    bin_file.write('P'.encode('utf-8'))
    bin_file.write('R'.encode('utf-8'))
    bin_file.write('L'.encode('utf-8'))
    bin_file.write('V'.encode('utf-8'))

    frame_header = random.randint(20, 40) << 20
    bin_file.write(struct.pack('<I', frame_header))


def add_packet_trailer(bin_file):
    bin_file.write('D'.encode('utf-8'))
    bin_file.write('N'.encode('utf-8'))
    bin_file.write('E'.encode('utf-8'))
    bin_file.write('V'.encode('utf-8'))


def add_random_data_packet(bin_file, packet_number):
    add_packet_header(bin_file)
    '''
    Header Definition:
    bits;   name;           value;  description;
    31:28   packet_type     0b0000   Signal Data Packet Type
    27      cbit            0       Class ID is not included in the packet
    26      isAck           0       This is not an Acknowledge packet
    25      reserved        1
    24      isCancellation  0       This is not a Calcellation packet
    23:22   tsi             00      Integer Timestamp definition
                                    00: Not included
                                    01: UTC time
                                    10 GPS time
                                    11: other (Base Set uses the custom epoch like Juliet)
    21:20   tsf             00      Fractional Timestamp definition
                                    00: Not included
                                    01: Sample Count
                                    10: picoseconds
                                    11: frequency running
    19:16   packet_count    0-15    Incrementing value for number of context packets in a set
    15:0    packet_size     0       The size of this packet is set to 0 actual size is stored in the first word
    '''
    header_start = 0b000000100000
    packet_size = 0b0000000000000000
    header = bin(int(str(header_start)[2:]) +
                 str(bin(packet_number))[2:].zfill(4) +
                 str(packet_size)[2:])
    bin_file.write(struct.pack('<I', header))

    bin_file.write(struct.pack('<I', packet_size))

    for _ in range(packet_size):
        sample_i = random.randint(-40, 40)
        sample_q = random.randint(-40, 40)
        bin_file.write(struct.pack('<h', sample_i))
        bin_file.write(struct.pack('<h', sample_q))

    add_packet_trailer(bin_file)


def add_random_context_packet(bin_file, packet_count, payload_size):
    add_packet_header(bin_file)
    '''
    Header Definition:
    bits;   name;           value;  description;
    31:28   packet_type     0b0101   Extension Context Packet Type
    27      cbit            0       Class ID is not included in the packet
    26      isAck           0       This is not an Acknowledge packet
    25      reserved        1
    24      isCancellation  0       This is not a Calcellation packet
    23:22   tsi             00      Integer Timestamp definition
                                    00: Not included
                                    01: UTC time
                                    10 GPS time
                                    11: other (Base Set uses the custom epoch like Juliet)
    21:20   tsf             00      Fractional Timestamp definition
                                    00: Not included
                                    01: Sample Count
                                    10: picoseconds
                                    11: frequency running
    19:16   packet_count    0-15    Incrementing value for number of context packets in a set
    15:0    packet_size     30+ user defined words  The size of this packet. 30 words
    '''
    header_start = 0b010100100000
    packet_size = 30
    header = bin(int(str(header_start)[2:]) +
                 str(bin(packet_count))[2:].zfill(4) +
                 str(bin(packet_size))[2:].zfill(16))
    bin_file.write(struct.pack('<I', header))
    '''
    Stream_ID will be provided by VAA upon allocation.
    '''
    stream_id = random.randint(11, 21)
    bin_file.write(struct.pack('<I', stream_id))

    '''
    CIF0 Definition
    31  cfci        0   Context Field change indicator
    30  rpi         0   Reference Point ID
    29  bandwidth   0   Bandwidth is incuded in this packet
    28 ifReffreq    0   IF Reference Frequency is not included in this packet
    27 rfRedfreq    0   RF Reference Frequency is included in this packet
    26 rfReffreqoffset  0   Offset from RF Reference Frequency to True RF Frequency is not included in this packet
    25 ifbandoffset 0   Offset from IF Reference Frequency to True IF Frequency is not included in this packet
    24 reflevel     0   Reference Level is not included in this packet
    23 gain         0   Gain is included in this packet
    22 overrangecount   0   Over Range Count is not included in this packet
    21 samplerate   0   Sample Rate is included in this packet
    20  tsa         0   Time Sample Adjustment is not included in this packet
    19  tscaltime   0   Timestamp Calibration Time is not included in this packet
    18  temp        0   Temperature is not included in this packet
    17  deviceid    0   Device ID is not included in this packet
    16  sei         0   State and Event Indicator is not included in this packet
    15  dataformat  0   Signal Data Packet Payload Format
                        0: Do not send a Signal Data Packet
                        1: Do send a Signal Data Packet
    14  gps         0   GPS is not included in this packet
    13  ins         0   Formatted INS is not included in this packet
    12  ecef        0   ECEF Ephemeris is not included in this packet
    11 relativeephemeris    0   Relative Ephemeris is not included in this packet
    10 ephemerisrefid       0   Ephemeris Reference ID is not included in this packet
    9 gpsascii              0   GPS in ASCII is not included in this packet
    8 contextpacketassoclists   0   Context Packet Association Lists are not included in this packet
    7 cif7enable    1   CIF7 is included in this packet
    6:5 reserved    00
    4   cif4enable  0   CIF4 is not included in this packet
    3   cif3enable  1   CIF3 is included in this packet
    2   cif2enable  0   CIF2 is not included in this packet
    1   cif1enable  0   CIF1 is not included in this packet
    0   reserved    0
    '''
    cif0 = 0b00000000000000000000000010001000
    bin_file.write(struct.pack('<I', cif0))

    '''
    CIF3 Definition
    '''
    cif3 = 0b00000000000000000000000100000000
    bin_file.write(struct.pack('<I', cif3))
    '''
    CIF7 Definition
    31:19   not reserved    0
    18:2    reserved        1
    1:0     reserved        0
    '''
    cif7 = 0b00000000000001111111111111111100
    bin_file.write(struct.pack('<I', cif7))

    field_a = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_a))

    field_b = random.randint(0, 100)
    bin_file.write(struct.pack('I', field_b))

    field_c = random.randint(0, 1024)
    bin_file.write(struct.pack('I', field_c))

    field_d = random.randint(0, 1024)
    bin_file.write(struct.pack('I', field_d))

    field_e = random.choice(
        [
            payload_size / 4,
            payload_size / 40,
            payload_size / 400,
            payload_size / 4000
        ]
    )
    bin_file.write(struct.pack('Q', field_e))

    field_f = random.gauss(1704067200000, 100000000000)
    bin_file.write(struct.pack('Q', field_f))

    field_g = random.randint(0, 5)
    bin_file.write(struct.pack('I', field_g))

    field_h = random.randint(0, 10)
    bin_file.write(struct.pack('I', field_h))

    field_i = random.uniform(0, 55)
    field_j = random.gauss(field_i, 0.01)
    bin_file.write(struct.pack('Q', field_j))

    bin_file.write(struct.pack('Q', field_i))

    field_k = random.gauss(field_j, 0.1)
    bin_file.write(struct.pack('Q', field_k))

    field_l = random.randint(0, 2147483648)
    bin_file.write(struct.pack('Q', field_l))

    pointing_elevation = random.randint(-90, 90)
    bin_file.write(struct.pack('<h', pointing_elevation))
    pointing_azimuth = random.randint(0, 511)
    bin_file.write(struct.pack('<h', pointing_azimuth))

    polarization_tilt_angle = random.choice([0, 12868])
    bin_file.write(struct.pack('<h', polarization_tilt_angle))
    polarization_ellpticity = random.choice([0, 12868, 6434])
    bin_file.write(struct.pack('<h', polarization_ellpticity))

    num_samples = payload_size / 4
    bin_file.write(struct.pack('I', num_samples))

    bin_file.write(struct.pack('I', payload_size))

    trailer_size = 0
    bin_file.write(struct.pack('I', trailer_size))

    user_defined_data_size = 0
    bin_file.write(struct.pack('I', user_defined_data_size))

    for _ in range(user_defined_data_size):
        user_defined_data = random.randint(0, 2048)
        bin_file.write(struct.pack('I', user_defined_data))

    add_packet_trailer(bin_file)


def add_random_extension_context_packet(bin_file):
    add_packet_header(bin_file)
    '''
    Header Definition:
    bits;   name;           value;  description;
    31:28   packet_type     0b0101   Extension Context Packet Type
    27      cbit            0       Class ID is not included in the packet
    26      isAck           0       This is not an Acknowledge packet
    25      reserved        1
    24      isCancellation  0       This is not a Calcellation packet
    23:22   tsi             00      Integer Timestamp definition
                                    00: Not included
                                    01: UTC time
                                    10 GPS time
                                    11: other (Base Set uses the custom epoch like Juliet)
    21:20   tsf             00      Fractional Timestamp definition
                                    00: Not included
                                    01: Sample Count
                                    10: picoseconds
                                    11: frequency running
    19:16   packet_count    1
    15:0    packet_size     26      The size of this packet. 30 words
    '''
    header_start = 0b0101001000000001
    packet_size = 26
    header = bin(int(str(header_start)[2:]) +
                 str(bin(packet_size))[2:].zfill(16))
    bin_file.write(struct.pack('<I', header))
    '''
    Stream_ID will be provided by VAA upon allocation.
    '''
    stream_id = random.randint(11, 21)
    bin_file.write(struct.pack('<I', stream_id))

    '''
    CIF0 Definition
    31  cfci        0   Context Field change indicator
    30  rpi         0   Reference Point ID
    29  bandwidth   0   Bandwidth is incuded in this packet
    28 ifReffreq    0   IF Reference Frequency is not included in this packet
    27 rfRedfreq    0   RF Reference Frequency is included in this packet
    26 rfReffreqoffset  0   Offset from RF Reference Frequency to True RF Frequency is not included in this packet
    25 ifbandoffset 0   Offset from IF Reference Frequency to True IF Frequency is not included in this packet
    24 reflevel     0   Reference Level is not included in this packet
    23 gain         0   Gain is included in this packet
    22 overrangecount   0   Over Range Count is not included in this packet
    21 samplerate   0   Sample Rate is included in this packet
    20  tsa         0   Time Sample Adjustment is not included in this packet
    19  tscaltime   0   Timestamp Calibration Time is not included in this packet
    18  temp        0   Temperature is not included in this packet
    17  deviceid    0   Device ID is not included in this packet
    16  sei         0   State and Event Indicator is not included in this packet
    15  dataformat  0   Signal Data Packet Payload Format
                        0: Do not send a Signal Data Packet
                        1: Do send a Signal Data Packet
    14  gps         0   GPS is not included in this packet
    13  ins         0   Formatted INS is not included in this packet
    12  ecef        0   ECEF Ephemeris is not included in this packet
    11 relativeephemeris    0   Relative Ephemeris is not included in this packet
    10 ephemerisrefid       0   Ephemeris Reference ID is not included in this packet
    9 gpsascii              0   GPS in ASCII is not included in this packet
    8 contextpacketassoclists   0   Context Packet Association Lists are not included in this packet
    7 cif7enable    0   CIF7 is not included in this packet
    6:5 reserved    00
    4   cif4enable  0   CIF4 is not included in this packet
    3   cif3enable  1   CIF3 is included in this packet
    2   cif2enable  0   CIF2 is not included in this packet
    1   cif1enable  1   CIF1 is included in this packet
    0   reserved    0
    '''
    cif0 = 0b00000000000000000000000000001010
    bin_file.write(struct.pack('<I', cif0))
    '''
    CIF1 Definition
    31  phaseoffset         0   Phase Offset is not included in this packet
    30  polarization        0   Polarization is included in this packet
    29  pointing3d          0   3d-pointing Vector is included in this packet
    28  pointing3dstruct    0   3d-pointing Vector Sctuct is not included in this packet
    27  spacialscantype     0   Spacial Scan Type is not included in this packet
    26  spacialreftype      0   Spacial Reference Type is not included in this packet
    25  beamwidth           1   Beam Width is incuded in this packet
    24  range               0   Range is not included in this packet
    23:21   reserved        111
    20  ber                 0   Bit Error Rate is not included in this packet
    19  threshold           0   Threshold is not included in this packet
    18  compressionpoint    0   Compression Point is not included in this packet
    17  ip2and3             0   Second and Thris order Intercept Points are not included in this packet
    16  snr                 0   SNR/Noise Figure is not included in this packet
    15  auxfreq             0   Auxillery Frequency is not included in this packet
    14  auxgain             0   Auxillery Gain is not included in this packet
    13  auxbandwidth        0   Auxillery Bandwidth is not included in this packet
    12  reserved            1
    11  cifarray            0   CIF Array is not included in this packet
    10  spectrum            0   Spectrum is not included in this packet
    9   scanstep            0   Scan Step is not included in this packet
    8   reserved            1
    7   indexlist           0   Index List is not included in this packet
    6   discreteio32        0   Discrete I/O 32-bits is not included in this packet
    5   discreteio64        0   Discrete I/O 64-bits is not included in this packet
    4   healthstatus        0   Health Status is not included in this packet
    3   v49compliance       0   This packet is not in compliance with the VITA 49 Spec
    2   version             0   VITA 49 version and Build Code are not included in this packet
    1   buffersize          0   Buffer Size is not included in this packet
    0   reserved            0
    '''
    cif1 = 0b00000000111000000001000100000000
    bin_file.write(struct.pack('<I', cif1))
    '''
    CIF3 Definition
    '''
    cif3 = 0b00110000000011001111100000000000
    bin_file.write(struct.pack('<I', cif3))

    field_a = 0XFFFFFFFF
    bin_file.write(struct.pack('I', field_a))

    field_b = 1
    bin_file.write(struct.pack('I', field_b))

    field_c = 4
    bin_file.write(struct.pack('I', field_c))

    field_d = 128
    bin_file.write(struct.pack('I', field_d))

    field_e = 1024
    bin_file.write(struct.pack('I', field_e))

    field_f = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_f))

    field_g = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_g))

    field_h = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_h))

    field_i = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_i))

    field_j = random.randint(0, 2147483648)
    bin_file.write(struct.pack('I', field_j))

    field_k = random.randint(0, 10)
    bin_file.write(struct.pack('I', field_k))

    field_l = random.randint(0, 10)
    bin_file.write(struct.pack('I', field_l))

    field_m = random.randint(0, 4294967296)
    bin_file.write(struct.pack('Q', field_m))

    field_n = 0x01001101000000000000000000000000
    bin_file.write(struct.pack('I', field_n))

    add_packet_trailer(bin_file)


def main():
    file_uuid = uuid.uuid4()
    file_name = f"MOCK_VITA_EXTENSION_DATA_{file_uuid}.bin"
    number_of_events = 10
    payload_size = 2621400
    data_packet_size = 65535

    with open(file_name, 'wb') as bin_file:
        add_random_extension_context_packet(bin_file)

        for i in range(number_of_events):
            add_random_context_packet(bin_file, i, payload_size)

        for j in range((number_of_events * payload_size) / data_packet_size):
            add_random_data_packet(bin_file, j % number_of_events)


if __name__ == "__main__":
    main()
