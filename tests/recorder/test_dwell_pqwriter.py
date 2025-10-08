import numpy as np
import pyarrow as pa
import pandas as pd
from bip.recorder.dwell.dwell_pqwriter import DwellPQWriter

def test_extension():
    assert DwellPQWriter.extension() == "parquet"


def test_create(tmp_path):
    out_path = tmp_path / "data"
    writer = DwellPQWriter(
        out_path,
        batch_size=3
    )

    out_dwell_file = out_path / "test_dwell-0.parquet"
    writer._current_sample_file = str(out_dwell_file)
    writer._record(end_of_dwell=False)

    assert out_dwell_file.exists()


def test_add_record(tmp_path):
    out_path = tmp_path / "data"

    writer = DwellPQWriter(
        out_path,
        batch_size=3
    )

    samples_i = np.arange(0, 10, dtype=np.int16)
    samples_q = np.arange(10, 20, dtype=np.int16)
    dwell_key = 23
    packet_data = 86
    packet_time = 0
    writer.add_record(
        {
            "samples_i": samples_i,
            "samples_q": samples_q,
            "time": packet_time,
            "packet_data": packet_data
        },
        dwell_key
    )

    writer.close()

    dwell_path = out_path / f"{dwell_key}-0.parquet"
    packet_data_path = out_path / "packet_data.parquet"
    dwell_metadata_path = out_path / "dwell_metadata.parquet"

    assert dwell_path.exists()
    assert packet_data_path.exists()
    assert dwell_metadata_path.exists()

    dwell_df = pd.read_parquet(dwell_path)
    assert (dwell_df.samples_i == samples_i).all()
    assert (dwell_df.samples_q == samples_q).all()

    packet_df = pd.read_parquet(packet_data_path)
    assert len(packet_df) == 1
    assert packet_df.packet_data.iloc[0] == packet_data
    assert packet_df.local_key.iloc[0] == dwell_key
    assert packet_df.time.iloc[0] == packet_time

    dwell_meta_df = pd.read_parquet(dwell_metadata_path)
    assert len(dwell_meta_df) == 1
    assert dwell_meta_df.local_key.iloc[0] == dwell_key
    assert dwell_meta_df.filename.iloc[0] == str(dwell_path)
    assert dwell_meta_df.first_record_index.iloc[0] == 0


def test_add_batch_single_dwell_in_order(tmp_path):
    out_path = tmp_path / "data"

    writer = DwellPQWriter(
        out_path,
        batch_size=3
    )

    n_packets = 10
    samples_i = [
        np.random.randint(0, 10, 10, dtype=np.int16)
        for _ in range(n_packets)
    ]
    samples_q = [
        np.random.randint(0, 10, 10, dtype=np.int16)
        for _ in range(n_packets)
    ]
    packet_data = [ np.random.randint(0, 10) for _ in range(n_packets) ]
    dwell_key=19

    for i in range(n_packets):
        writer.add_record(
            {
                "samples_i": samples_i[i],
                "samples_q": samples_q[i],
                "time": i,
                "packet_data": packet_data[i]
            },
            dwell_key
        )

    writer.close()

    dwell_path = out_path / f"{dwell_key}-0.parquet"
    packet_data_path = out_path / "packet_data.parquet"
    dwell_metadata_path = out_path / "dwell_metadata.parquet"

    dwell_df = pd.read_parquet(dwell_path)
    assert (dwell_df.samples_i == np.concatenate(samples_i)).all()
    assert (dwell_df.samples_q == np.concatenate(samples_q)).all()

    packet_df = pd.read_parquet(packet_data_path)
    assert len(packet_df) == n_packets
    assert (packet_df.packet_data == packet_data).all()
    assert (packet_df.local_key == dwell_key).all()
    assert (packet_df.time == list(range(n_packets))).all()

    dwell_meta_df = pd.read_parquet(dwell_metadata_path)
    assert len(dwell_meta_df) == 1
    assert dwell_meta_df.local_key.iloc[0] == dwell_key
    assert dwell_meta_df.filename.iloc[0] == str(dwell_path)
    assert dwell_meta_df.first_record_index.iloc[0] == 0


def test_add_batch_multiple_dwells_in_order(tmp_path):
    out_path = tmp_path / "data"

    writer = DwellPQWriter(
        out_path,
        batch_size=3
    )

    n_packets_per_dwell = 5
    n_dwells = 3
    n_samples_per_packet = 5
    n_packets = n_packets_per_dwell * n_dwells

    # not generating these randomly because they must be different.
    dwell_keys = [18, 40, 25]
    dwell_samples_i = { k : [] for k in dwell_keys }
    dwell_samples_q = { k : [] for k in dwell_keys }
    first_dwell_packet_numbers = {}
    total_packets = 0
    packet_data = np.random.randint(0, 10, n_packets)

    for i in range(n_dwells):
        dwell_key = dwell_keys[i]
        first_dwell_packet_numbers[dwell_key] = total_packets

        for _ in range(n_packets_per_dwell):
            samples_i = np.random.randint(-10, 10, n_samples_per_packet, dtype=np.int16)
            samples_q = np.random.randint(-10, 10, n_samples_per_packet, dtype=np.int16)
            dwell_samples_i[dwell_key].append(samples_i)
            dwell_samples_q[dwell_key].append(samples_q)

            writer.add_record(
                {
                    "samples_i": samples_i,
                    "samples_q": samples_q,
                    "time": total_packets,
                    "packet_data": packet_data[total_packets]
                },
                dwell_key
            )

            total_packets += 1

    writer.close()

    packet_data_path = out_path / "packet_data.parquet"
    dwell_metadata_path = out_path / "dwell_metadata.parquet"

    packet_df = pd.read_parquet(packet_data_path)
    assert len(packet_df) == n_packets
    assert (packet_df.packet_data == packet_data).all()
    assert (packet_df.time == list(range(n_packets))).all()
    expected_keys = sum([ [key] * n_packets_per_dwell for key in dwell_keys], [])
    assert (packet_df.local_key == expected_keys).all()

    dwell_meta_df = pd.read_parquet(dwell_metadata_path)
    assert len(dwell_meta_df) == n_dwells
    assert (dwell_meta_df.local_key == dwell_keys).all()
    assert all(
        first_dwell_packet_numbers[row.local_key] == row.first_record_index
        for row in dwell_meta_df.itertuples()
    )
    assert all(
        (out_path / row.filename).exists()
        for row in dwell_meta_df.itertuples()
    )

    for row in dwell_meta_df.itertuples():
        dwell_key = row.local_key
        dwell_df = pd.read_parquet(row.filename)
        assert (dwell_df.samples_i == np.concat(dwell_samples_i[dwell_key])).all()
        assert (dwell_df.samples_q == np.concat(dwell_samples_q[dwell_key])).all()


def test_recorder_writes_on_delete(tmp_path):
    file_ = tmp_path / "test_data_dir"

    writer = DwellPQWriter(
        file_,
        batch_size = 3
    )

    for i in range(1):
        writer.add_record({
            "id": np.int32(i),
            "val": np.int32(i),
            "samples_i": np.zeros(1),
            "samples_q": np.zeros(1),
            "time": 0
        })

    # Writer should not have created the parquet file because
    # fewer than `batch_size` records have been written.
    assert not file_.exists()

    del writer

    assert file_.exists()

    # Make sure this is a valid parquet file
    pd.read_parquet(file_)
