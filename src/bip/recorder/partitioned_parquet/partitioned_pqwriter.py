from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from bip.recorder.parquet.pqwriter import PQWriter


class PartitionedPQWriter(PQWriter):
    def __init__(self,
                 filename: Path,
                 schema: pa.schema,
                 partition_cols,
                 options: dict = {},
                 batch_size: int = 1000,
                 ):
        """
        `existing_data_behavior` can be any of:
            "delete_matching" - delete an existing dataset at the same path
            "overwrite_or_ignore" - append to existing data at the same path
            "error" - raise an error if data exists at the same path

        `options['partition_cols'] MUST be set for this recorder
        """

        super(
            PartitionedPQWriter,
            self).__init__(
            filename,
            schema,
            options,
            batch_size)

        self._partition_cols = partition_cols

    def _record(self):
        df = pd.DataFrame(self.data)
        table = pa.Table.from_pandas(df)
        pq.write_to_dataset(
            table,
            self._filename,
            schema=self.schema,
            existing_data_behavior="overwrite_or_ignore",
            partition_cols=self._partition_cols,
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


def new_partitioned_parquet_writer(
    partition_cols
):
    def constructor(filename, schema, options={}, batch_size=1000):
        return PartitionedPQWriter(
            filename,
            schema,
            partition_cols,
            options=options,
            batch_size=batch_size
        )

    constructor.extension = PartitionedPQWriter.extension

    return constructor
