from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class PQWriter:
    @staticmethod
    def extension() -> str:
        return "parquet"

    def __init__(self,
                 filename: Path,
                 schema: pa.schema,
                 options: dict = {},
                 batch_size: int = 1000
                 ):

        self._closed = False

        self._filename = filename
        self._schema = schema
        self._options = options.copy()

        self.batch_size = batch_size
        self.schema = schema
        self.data = []
        self.writer = None
        self.current_index = 0

        # terrible, horrible, no good, very bad hack.
        if "partition_cols" in self._options:
            del self._options['partition_cols']

    def _record(self):
        df = pd.DataFrame(self.data)
        table = pa.Table.from_pandas(df)
        try:
            if self.writer is None:
                self.writer = pq.ParquetWriter(
                    self._filename, self.schema, **self._options)
            self.writer.write_table(table)
        except Exception as e:
            print(f"Error writing file: {e}, {self._filename}")

        self.data = []
        self.current_index = 0

    def add_record(self, record: dict):
        assert self.current_index < self.batch_size
        self.data.append(record)
        self.current_index += 1
        if self.current_index == self.batch_size:
            self._record()

    def close(self):
        if self._closed:
            return

        if self.current_index != 0:
            self._record()

        self.writer.close()
        self._closed = True

    @property
    def metadata(self) -> dict:
        return {
            "output": str(self._filename),
            "options": self._options,
            "batch_size": self.batch_size
        }

    def __del__(self):
        if not self._closed:
            self.close()
