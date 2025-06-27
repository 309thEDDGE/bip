import struct
import random
import uuid


def add_random_data_packet(bin_file, payload_size, trailer_size):

    bin_file.write(struct.pack('I', payload_size))

    for _ in range(payload_size / 4):
        sample_i = random.randint(-40, 40)
        sample_q = random.randint(-40, 40)
        bin_file.write(struct.pack('<h', sample_i))
        bin_file.write(struct.pack('<h', sample_q))

    for _ in range(trailer_size):
        trailer_data = 0xAAAAAAAA
        bin_file.write(struct.pack('I', trailer_data))


def add_random_job_interval_header(bin_file):
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


def add_random_job_event_header(bin_file, payload_size, trailer_size):
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

    bin_file.write(struct.pack('I', trailer_size))

    user_defined_data_size = 3
    bin_file.write(struct.pack('I', user_defined_data_size))

    for _ in range(user_defined_data_size):
        user_defined_data = random.randint(0, 2048)
        bin_file.write(struct.pack('I', user_defined_data))


def main():
    file_uuid = uuid.uuid4()
    file_name = f"MOCK_JOB_FORMAT_DATA_{file_uuid}.bin"
    job_events = 10

    with open(file_name, 'wb') as bin_file:
        add_random_job_interval_header(bin_file)

        trailer_size = 0
        payload_size = 262140
        for _ in range(job_events):
            add_random_job_event_header(bin_file, payload_size, trailer_size)

        for _ in range(job_events):
            add_random_data_packet(bin_file, payload_size, trailer_size)


if __name__ == "__main__":
    main()
