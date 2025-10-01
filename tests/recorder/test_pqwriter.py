import numpy as np
import pyarrow as pa
import pandas as pd
from bip.recorder.parquet.pqwriter import PQWriter


def test_extension():
    assert PQWriter.extension() == "parquet"


def test_create(tmp_path):
    file_ = tmp_path / "test.parquet"

    parquetwriter = PQWriter(file_,
            pa.schema([("id", pa.int32()), ("val", pa.int32())]),
            {},
            batch_size = 3)
    parquetwriter._record() #Accessing an _ funciton like this is bad practice
    parquetwriter.close()

    assert file_.exists()


def test_add_record(tmp_path):
    file_ = tmp_path / "test.parquet"

    writer = PQWriter(file_,
            pa.schema([("id", pa.int32()), ("val", pa.int32())]),
            {},
            batch_size = 3)

    writer.add_record({"id": np.int32(1), "val": np.int32(1)})
    writer.close()

    assert file_.exists()
    df = pd.read_parquet(file_)
    assert len(df) == 1
    assert df.id.iloc[0] == 1
    assert df.val.iloc[0] == 1


def test_add_batch(tmp_path):
    file_ = tmp_path / "test.parquet"

    writer = PQWriter(file_,
            pa.schema([("id", pa.int32()), ("val", pa.int32())]),
            {},
            batch_size = 3)

    for i in range(10):
        writer.add_record({"id": np.int32(i), "val": np.int32(i)})
    writer.close()

    assert file_.exists()
    df = pd.read_parquet(file_)
    assert (df.id.to_numpy() == np.array(range(10), dtype=np.int32)).all()
    assert (df.val.to_numpy() == np.array(range(10), dtype=np.int32)).all()


def test_zip(tmp_path):
    file_ = tmp_path / "test.parquet"

    writer = PQWriter(file_,
            pa.schema([("id", pa.int32()), ("val", pa.int32())]),
            options={"compression": "GZIP", "compression_level": 5},
            batch_size = 3)

    for i in range(10):
        writer.add_record({"id": np.int32(i), "val": np.int32(i)})
    writer.close()

    assert file_.exists()
    df = pd.read_parquet(file_)
    assert (df.id.to_numpy() == np.array(range(10), dtype=np.int32)).all()
    assert (df.val.to_numpy() == np.array(range(10), dtype=np.int32)).all()


def test_metadata(tmp_path):
    file_ = tmp_path / "test.parquet"

    writer = PQWriter(file_,
            pa.schema([("id", pa.int32()), ("val", pa.int32())]),
            options={"compression": "GZIP", "compression_level": 5},
            batch_size = 3)

    for i in range(1):
        writer.add_record({"id": np.int32(i), "val": np.int32(i)})
    writer.close()

    metadata = writer.metadata
    assert metadata["output"] == str(file_)
    assert metadata["batch_size"] == 3
    assert metadata["options"]["compression"] == "GZIP"
    assert metadata["options"]["compression_level"] == 5
