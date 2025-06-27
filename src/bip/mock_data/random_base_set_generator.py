import struct
import random
import uuid


def create_random_metadata():
    metadata = {}
    metadata.update({'A': '0'})
    metadata.update({'B': '0'})
    metadata.update({'C': '0'})
    metadata.update({'D': '0'})
    metadata.update({'E': '0'})
    metadata.update({'F': '0'})
    metadata.update({'G': '0'})
    metadata.update({'H': '0'})
    metadata.update({'I': '0'})
    metadata.update({'J': '0'})
    metadata.update({'K': []})
    metadata.update({'L': []})
    metadata.update({'M': []})
    metadata.update({'N': []})

    return metadata


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


def add_random_data_packet(bin_file):
    add_packet_header(bin_file)
    packet_size = 65535
    packet_id = random.randint(7000, 8000)
    bin_file.write(struct.pack('H', packet_size))
    bin_file.write(struct.pack('H', packet_id))
    stream_id = random.randint(11, 21)
    bin_file.write(struct.pack('<I', stream_id))
    class_id_0 = 0x00AAAAAA
    bin_file.write(struct.pack('<I', class_id_0))
    class_id_1 = 0X04000D00
    bin_file.write(struct.pack('<I', class_id_1))
    tsi = random.randint(1690000000, 1700000000)
    bin_file.write(struct.pack('<I', tsi))
    tsf = random.randint(0, 18000000000000000000)
    bin_file.write(struct.pack('<Q', tsf))

    for _ in range(65534):
        sample_i = random.randint(-40, 40)
        sample_q = random.randint(-40, 40)
        bin_file.write(struct.pack('<h', sample_i))
        bin_file.write(struct.pack('<h', sample_q))

    add_packet_trailer(bin_file)


def add_random_context_packet(bin_file):
    add_packet_header(bin_file)
    '''
    Base Set Header Definition:
    bits;   name;           value;  description;
    31:28   packet_type     0b0111   Extension Command Packet Type
    27      cbit            1       Class ID is included in the packet
    26      isAck           0       This is not an Acknowledge packet
    25      reserved        0
    24      isCancellation  0       This is not a Calcellation packet
    23:22   tsi             11      Integer Timestamp definition
                                    00: Not included
                                    01: UTC time
                                    10 GPS time
                                    11: other (Base Set uses the custom epoch like Juliet)
    21:20   tsf             10      Fractional Timestamp definition
                                    00: Not included
                                    01: Sample Count
                                    10: picoseconds
                                    11: frequency running
    19:16   packet_count    0-15    Incrementing value for number of context packets in a set
    15:0    packet_size     32      The size of this packet. 32 words
    '''
    header = 0b01111000111000010000000000100000
    bin_file.write(struct.pack('<I', header))
    '''
    Stream_ID will be provided by VAA upon allocation.
    '''
    stream_id = random.randint(11, 21)
    bin_file.write(struct.pack('<I', stream_id))
    '''
    Class ID Definition:
    31:27   padbitcount             0   Number of padding bits added at the end of the packet
    26:24   reserved                0
    23:0    oui                     0xAAAAAA  OCS organization number. This is IEEE defined per vendor

    31:24   info_class_code_type    4 or 5  The Class Code for the Information in this packet.
                                            0: unknown
                                            1: Tx
                                            2: Rx
                                            3: Sensor
                                            4: Tx Base Set compliant
                                            5: Rx Base Set compliant
                                            6: Tx Base Set Extension 1 compliant
                                            7: Rx Base Set Extension 1 compliant
                                            8: Tx Base Set Extension 2 complaint
                                            9: Rx Base Set Extension 2 compliant
                                            10-255: undefined
    23:16   info_class_code_version 0-255   The version of the Information Class Code in case Base Set changes
    15:8    packet_class_code_type  0x0A    The Class Code for the Packet itself.
                                            00: undefined
                                            0A: Base Set Control Schedule Request
                                            0B: Base Set Schedule Acknowledge
                                            0C: Base Set Execution Acknowledge
                                            0D: Base Set Data
                                            0E: Base Set Data Context
    7:0     packet_class_code_version 0-255 The version of the Packet Class Code in case the definitions change
    '''
    class_id_0 = 0x00AAAAAA
    bin_file.write(struct.pack('<I', class_id_0))
    class_id_1 = 0x04000A00
    bin_file.write(struct.pack('<I', class_id_1))
    tsi = random.randint(1690000000, 1700000000)
    bin_file.write(struct.pack('<I', tsi))
    tsf = random.randint(0, 18000000000000000000)
    bin_file.write(struct.pack('<Q', tsf))

    '''
    Control Ack Mode Field Definition:
    31      ce          0   Controllee ID is not included in this packet
    30      ie          0   Controllee ID format is not included in this packet
    29      cr          0   Controller ID is not included in this packet
    28      ir          0   Controller ID format is not included in this packet
    27      p           0   Partial packet execustion Permission
                            0: Any uncorrected errors and warnings will cause the whole packet to be rejected
                            1: Any parameter without error will be executed and and errored parameter will execute
                               if corrected
    26      w           0   What happens when a warning occcurs
                            0: no action (Base Set has no warnings at all, only errors)
                            1: MFA will try to correct the parameter
    25      er          0   What happends when an error occurs
                            0: no action
                            1: MFA will try to correct the parameter
    24:23   actionbits  10  What will this packet do
                            00: no action
                            01: dry run
                            10: execute
                            11: undefined
    22      nack        0   Do not Provide negative acknowledgements when warnings/errors occur. 1: would do that
    21      reserved    0
    20      reqv        0   Validation Ack Packet not requested
    19      reqx        1   Execution Ack packet is requested
    18      reqs        0   Query-State Ack packet not requested
    17      reqw        0   Do not include Warning Fields in Execution and Validation packets
    16      reqEr       1   Do include Error Fields in Execution Packets
    15      reqR        1   Info-Response packet is requested
    14:12   timingcontrol   000 Timing control is at Controllee's discretion, default is when Control Fields are
                                executed
    11:8    ackbits     0   Acknowledge bits
    7:4     Schreqtype  1   Schedule Request Type
                            0: None. Message is for information only. Timestamp is time after which the scheduler can
                               expect to receive schedule requests
                            1: Requesting execute starting at Timestamp for Dwell seconds
                            2: Requesting execute start between Timestamp + Early_Start and Timestamp + Late_Start
                               for Dwell seconds
                            3: Requesting execute when possible starting now for Dwell seconds
                            4-14: undefined
                            15: Cancel
    3       reqStatuschange 0   This packet is not requesting a status change
    2:0     reserved    0
    '''
    control_ack_mode_field = 0b00000001000010011000000000010000
    bin_file.write(struct.pack('<I', control_ack_mode_field))
    '''
    Message ID
    This is used to distinguish Context Packets with the same Stream ID and Class ID values.
    This value increments starting at 1
    '''
    message_id = 1
    bin_file.write(struct.pack('<I', message_id))
    '''
    CIF0 Definition
    31  cfci        1   Context Field change indicator
    30  rpi         0   Reference Point ID
    29  bandwidth   1   Bandwidth is incuded in this packet
    28 ifReffreq    0   IF Reference Frequency is not included in this packet
    27 rfRedfreq    1   RF Reference Frequency is included in this packet
    26 rfReffreqoffset  0   Offset from RF Reference Frequency to True RF Frequency is not included in this packet
    25 ifbandoffset 0   Offset from IF Reference Frequency to True IF Frequency is not included in this packet
    24 reflevel     0   Reference Level is not included in this packet
    23 gain         1   Gain is included in this packet
    22 overrangecount   0   Over Range Count is not included in this packet
    21 samplerate   1   Sample Rate is included in this packet
    20  tsa         0   Time Sample Adjustment is not included in this packet
    19  tscaltime   0   Timestamp Calibration Time is not included in this packet
    18  temp        0   Temperature is not included in this packet
    17  deviceid    0   Device ID is not included in this packet
    16  sei         0   State and Event Indicator is not included in this packet
    15  dataformat  1   Signal Data Packet Payload Format
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
    4   cif4enable  1   CIF4 is included in this packet
    3   cif3enable  1   CIF3 is included in this packet
    2   cif2enable  1   CIF2 is included in this packet
    1   cif1enable  1   CIF1 is included in this packet
    0   reserved    0
    '''
    cif0 = 0b10101000101000001000000000011110
    bin_file.write(struct.pack('<I', cif0))
    '''
    CIF1 Definition
    31  phaseoffset         0   Phase Offset is not included in this packet
    30  polarization        1   Polarization is included in this packet
    29  pointing3d          1   3d-pointing Vector is included in this packet
    28  pointing3dstruct    0   3d-pointing Vector Sctuct is not included in this packet
    27  spacialscantype     0   Spacial Scan Type is not included in this packet
    26  spacialreftype      0   Spacial Reference Type is not included in this packet
    25  beamwidth           1   Beam Width is incuded in this packet
    24  range               0   Range is not included in this packet
    23:21   reserved        000
    20  ber                 0   Bit Error Rate is not included in this packet
    19  threshold           0   Threshold is not included in this packet
    18  compressionpoint    0   Compression Point is not included in this packet
    17  ip2and3             0   Second and Thris order Intercept Points are not included in this packet
    16  snr                 0   SNR/Noise Figure is not included in this packet
    15  auxfreq             0   Auxillery Frequency is not included in this packet
    14  auxgain             0   Auxillery Gain is not included in this packet
    13  auxbandwidth        0   Auxillery Bandwidth is not included in this packet
    12  reserved            0
    11  cifarray            0   CIF Array is not included in this packet
    10  spectrum            0   Spectrum is not included in this packet
    9   scanstep            0   Scan Step is not included in this packet
    8   reserved            0
    7   indexlist           0   Index List is not included in this packet
    6   discreteio32        0   Discrete I/O 32-bits is not included in this packet
    5   discreteio64        0   Discrete I/O 64-bits is not included in this packet
    4   healthstatus        0   Health Status is not included in this packet
    3   v49compliance       0   This packet is not in compliance with the VITA 49 Spec
    2   version             0   VITA 49 version and Build Code are not included in this packet
    1   buffersize          0   Buffer Size is not included in this packet
    0   reserved            0
    '''
    cif1 = 0b01100010000000000000000000000000
    bin_file.write(struct.pack('<I', cif1))
    '''
    CIF2 Definition:
    31:7 All 0s not in my notebook
    6   funcpriorityID  1   Function Priority ID is included in the packet
    5:0 All 0s not in my notebook
    '''
    cif2 = 0b00000000000000000000000001000000
    bin_file.write(struct.pack('<I', cif2))
    '''
    CIF3 Definition
    31:22 All 0s not in my notebook
    21 dwell        1       Dwell Duration is included in the packet
    20:0    All 0s not in my notebook
    '''
    cif3 = 0b00000000001000000000000000000000
    bin_file.write(struct.pack('<I', cif3))
    '''
    CIF4 Definition
    31:30   reserved    0
    29  rffigureofmerit 1   For an Rx Packet this means the Requested Input dB/k Range is included in this packet
                            For a Tx Packet this means that the EIRP in dBM is included in this packet
    28  earlystarttime  0   Early Start Time is not included in this packet
    27  latestarttime   0   Late Start Time is not included in this packet
    26  rejectreason    0   Reject Reason is not included in this packet
    25  maxdatapacketdwell  0   Max Data Packet Dwell is not included in this packet
    24  addressgroupindex   1   Address Group Index is included in this packet
    23  dataaddressstructure    0   Data Address Structure is not included in this packet
    22  dataaddresstime     0   Data Address Time is not included in this packet
    21  txdigitalinputpower 1   Tx Digital Input Power is included in this packet
    20:0    reserved        0
    '''
    cif4 = 0b00100001001000000000000000000000
    bin_file.write(struct.pack('<I', cif4))

    bandwidth = random.uniform(0.00, 8.79)
    bin_file.write(struct.pack('<d', bandwidth))
    rf_freq = random.uniform(0, 55)
    bin_file.write(struct.pack('<d', rf_freq))
    '''
    Note about Gain
    Gain 31:16 are set to 0 in Base Set
    Gain 15:0 is used in Base Set Rx Schedule Requests to control signal amplitude into MFA ADC
    Gain 15:0 Will be set to 0 in Tx Schedule Requests
    '''
    gain1 = 0
    bin_file.write(struct.pack('<h', gain1))
    gain2 = random.randint(-256, 256)
    bin_file.write(struct.pack('<h', gain2))
    '''
    Sample Rate is measured in Hz'''
    sample_rate = 80
    bin_file.write(struct.pack('<Q', sample_rate))

    data_format = 900
    bin_file.write(struct.pack('<Q', data_format))
    '''
    Notes on Polarization
    Polarization 31:16 are ellipse tilt angle
    Polarization 15:0 are ellipse eccentricity both measured in radians

    Tilt Angle: angle of the polarization ellipse major axis counter clockwise from the antenna plane's positive
                x-axis

    Ellipticity: eccentricity of polarization ellipse including rotation direction
    Ellipticity=0: Right-handed circular polarization
    Ellipticity=pi/2: Left-handed circular polarization
    Ellipticity=pi/4: Linear polarization
        tilt = 0: Linear means Horizontal
        tilt = pi/2: Linear means Vertical

    Left/Right Handedness are defined from the POV of an observer at the receiver looking towards the transmitter

    The direction in which tilt angle is measured and the definitions of left/right handed rotation are not
    consistent with IEEE standard 145-1993 and that makes me sad
    '''
    polarization_tilt_angle = random.choice([0, 12868])
    bin_file.write(struct.pack('<h', polarization_tilt_angle))
    polarization_ellpticity = random.choice([0, 12868, 6434])
    bin_file.write(struct.pack('<h', polarization_ellpticity))
    '''
    Notes on the 3d-Pointing Vector
    31:16 are Elevation
    15:0 are Azimuth
    Both are measured from the antenna's frame of reference

    Antenna boresight is the z-axis
    x-axis is orthogonal to z and is horizontal
    y-axis points up in the antenna's frame of reference 90deg clockwise from x-axis

    Elevation is measured up +y from x-z plane
    Azimuth is measured in x-z between projection of pointing vector onto x-z and boresight
    Positive Azimuth is clockwise from boresight looking down
    '''
    pointing_elevation = random.randint(-90, 90)
    bin_file.write(struct.pack('<h', pointing_elevation))
    pointing_azimuth = random.randint(0, 511)
    bin_file.write(struct.pack('<H', pointing_azimuth))

    '''
    Beam Width refers to the exact value in Base Set, but other interpretations are acknowledged for possible
    extensions

    Beam Width could refer to the maximum allowable Beam Width
    Beam Width could refer to the minimum allowable Beam Width

    This is only point in the base set that different interpretations of a field are noted, so I am noting it
    down here
    '''
    beam_width_vert = random.randint(0, 360)
    bin_file.write(struct.pack('<H', beam_width_vert))
    beam_width_horiz = random.randint(0, 360)
    bin_file.write(struct.pack('<H', beam_width_horiz))

    '''
    Function Priority ID is used to resolve conflicting requests to use the MFA
    This is the spot in line that this context packet wants to be in
    '''
    function_priority_id = random.randint(0, 67108864)
    bin_file.write(struct.pack('<I', function_priority_id))

    '''
    Dwell Duration is measured in femtoseconds
    This is the duration of the requested event
    Dwells can be between 0-9223 seconds (2 hours 33 minutes 43 seconds)
    '''
    dwell_duration = 4000000000000000
    bin_file.write(struct.pack('<Q', dwell_duration))

    '''
    Effective Isotropic Radiated Power (EIRP) is the hypothetical power that
    would have to be radiated by an isotrpoic antenna to give the same signal strength
    as the actual souce antenna in the direction of the antenna's strongest beam
    EIRP is expressed in dBm decibel-milliwatts
    '''
    EIRP = random.randint(0, 10)
    bin_file.write(struct.pack('<I', EIRP))

    '''
    Address Group Index is a look-up index that points to a collection of MFP addresses
    for data and Ack packets for this request
    '''
    address_group_index = random.randint(0, 2147483647)
    bin_file.write(struct.pack('<I', address_group_index))

    '''
    Tx Digital Input Power
    31:16 will be set to 0
    15:0 contain nominal power level of digital Tx signal input to MFA
    '''
    digital_input_power_0 = 0
    bin_file.write(struct.pack('<H', digital_input_power_0))
    digital_input_power_1 = random.randint(0, 65535)
    bin_file.write(struct.pack('<H', digital_input_power_1))

    add_packet_trailer(bin_file)


def main():
    file_uuid = uuid.uuid4()
    file_name = f"MOCK_BASE_SET_DATA_{file_uuid}.bin"

    create_random_metadata()

    with open(file_name, 'wb') as bin_file:
        for _ in range(10):
            add_random_context_packet(bin_file)

            for _ in range(400):
                add_random_data_packet(bin_file)


if __name__ == "__main__":
    main()
