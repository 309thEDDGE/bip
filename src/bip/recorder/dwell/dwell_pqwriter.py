from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import heapq
import os

from ..parquet.pqwriter import PQWriter

import numpy as np

samples_schema = pa.schema([
    ("samples_i", pa.int16()),
    ("samples_q", pa.int16())
])


class DwellPQWriter:
    @staticmethod
    def extension() -> str:
        return "parquet"

    def __init__(self,
                 filename: Path,
                 schema: pa.schema = None,
                 options: dict = {},
                 batch_size: int = 1000
                 ):

        self._filename = filename
        self._schema = schema
        self._options = options.copy()
        self._closed = False

        self.batch_size = batch_size

        self._dirname = filename.with_suffix("")
        self._dirname.mkdir(exist_ok=True)

        self.sample_data_i = []
        self.sample_data_q = []
        self.written_keys = {}
        self.current_index = 0
        self.sample_writer = None
        self.packet_writer = PQWriter(
            self._dirname / "packet_data.parquet",
            options=self._options
        )
        self.dwell_metadata_writer = PQWriter(
            self._dirname / "dwell_metadata.parquet",
            options=self._options
        )

        self.last_packet_time = 0

        self._current_local_key = -1
        self._current_sample_file = None

        self.records_counted = 0

    def _record(self, end_of_dwell: bool):
        if self.sample_data_i:
            sample_i_array = np.concatenate([i for _, i in self.sample_data_i])
            sample_q_array = np.concatenate([q for _, q in self.sample_data_q])
        else:
            sample_i_array = np.zeros(0, dtype=np.int16)
            sample_q_array = np.zeros(0, dtype=np.int16)

        samples_df = pd.DataFrame(
            {
                "samples_i": sample_i_array,
                "samples_q": sample_q_array
            }
        )
        samples_table = pa.Table.from_pandas(samples_df)

        if self.sample_writer is None:
            self.sample_writer = pq.ParquetWriter(
                self._current_sample_file,
                samples_schema
            )

        self.sample_writer.write_table(samples_table)

        if end_of_dwell:
            self.sample_writer.close()
            self.sample_writer = None

        # clear out written data
        self.packet_data = []
        self.dwell_metadata = []
        self.sample_data_i = []
        self.sample_data_q = []

    def add_record(self, record: dict, dwell_key: int = None):
        local_key = dwell_key

        if local_key != self._current_local_key:
            if self._current_local_key != -1:
                # This is data for a new dwell, so write out all the
                # data for the current dwell before starting on this one.
                self._record(end_of_dwell=True)

            # If we've written data for this local key before,
            # then we'll have to write the rest of the data to a new file.
            if local_key not in self.written_keys:
                self.written_keys[local_key] = 0
                times_key_written = 0
            else:
                times_key_written = self.written_keys[local_key]
                times_key_written += 1
                self.written_keys[local_key] = times_key_written

            suffix = str(times_key_written)

            iq_data_filename = f"{str(local_key)}-{suffix}.parquet"
            self._current_sample_file = os.path.join(self._dirname,
                                                     iq_data_filename)

            self.dwell_metadata_writer.add_record(
                {
                    "local_key": local_key,
                    "filename": self._current_sample_file,
                    "first_record_index": self.records_counted
                }
            )

            self._current_local_key = local_key
            self.last_packet_time = 0

        record["local_key"] = dwell_key
        self.last_packet_time = record["time"]

        heapq.heappush(self.sample_data_i,
                       (record["time"], record.pop("samples_i")))
        heapq.heappush(self.sample_data_q,
                       (record["time"], record.pop("samples_q")))
        self.packet_writer.add_record(record)

        self.current_index += 1
        self.records_counted += 1
        if self.current_index == self.batch_size:
            self.current_index = 0
            self._record(end_of_dwell=False)

    def close(self):
        if self._closed:
            return

        if self.records_counted != 0:
            self._record(end_of_dwell=True)

        self.packet_writer.close()
        self.dwell_metadata_writer.close()

        self._closed = True

    @property
    def metadata(self) -> dict:
        return {
            "output": str(self._filename),
            "options": self._options,
            "batch_size": self.batch_size
        }
