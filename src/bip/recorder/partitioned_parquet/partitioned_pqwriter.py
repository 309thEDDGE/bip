from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from bip.recorder.parquet.pqwriter import PQWriter


class PartitionedPQWriter(PQWriter):
    def __init__(
        self,
        filename: Path,
        schema: pa.schema,
        options: dict = None,
        batch_size: int = 1000,
    ):
        """
        `existing_data_behavior` can be any of:
            "delete_matching" - delete an existing dataset at the same path
            "overwrite_or_ignore" - append to existing data at the same path
            "error" - raise an error if data exists at the same path

        `options['partition_cols'] MUST be set for this recorder
        """

        super(PartitionedPQWriter, self).__init__(
            filename,
            schema,
            options,
            batch_size
        )

    def add_record(self, record, dwell_key: int = None):
        # deal with Nones
        dwell_key = dwell_key or 0
        record["data_key"] = dwell_key
        return super().add_record(record, dwell_key)

    def _record(self):
        df = pd.DataFrame(self.data)
        table = pa.Table.from_pandas(df)
        pq.write_to_dataset(
            table,
            self._filename,
            schema=self.schema,
            existing_data_behavior="overwrite_or_ignore",
            partition_cols=["data_key"],
            **self._options
        )

        self.data = []
        self.current_index = 0

    def close(self):
        if self._closed:
            return

        if self.current_index != 0:
            self._record()

        self._closed = True
