from pathlib import Path
import pyarrow as pa

from .dwell_pqwriter import DwellPQWriter

samples_schema = pa.schema([
    ("samples_i", pa.int16()),
    ("samples_q", pa.int16())
])


class MikelimaDwellPQWriter:
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

        self._dirname = filename.parent

        self.written_keys = {}

        self.sample_writer_inner = DwellPQWriter(
            self._dirname / "data",
            options=self._options,
            batch_size=batch_size
        )

        self.batch_size = batch_size
        self.record_count = 0

    @staticmethod
    def extract_sample_type(record, samples_mapping, unused_keys):
        record = record.copy()

        for unused_samples in unused_keys:
            if unused_samples in record:
                del record[unused_samples]

        for samples_old, samples_new in samples_mapping.items():
            record[samples_new] = record[samples_old]
            del record[samples_old]

        return record

    def add_record(self, record: dict, dwell_key: int = None):
        # split record, which contains samples for left right and possibly
        # center sample types, into one record for each sample type.

        left_samples_map = {
            "samples_i_left": "samples_i",
            "samples_q_left": "samples_q"
        }
        right_samples_map = {
            "samples_i_right": "samples_i",
            "samples_q_right": "samples_q"
        }
        center_samples_map = {
            "samples_i_center": "samples_i",
            "samples_q_center": "samples_q"
        }

        # this works, trust me
        dwell_key_left = self.record_count * 3
        dwell_key_right = self.record_count * 3 + 1
        dwell_key_center = self.record_count * 3 + 2

        left_record = MikelimaDwellPQWriter.extract_sample_type(
            record,
            left_samples_map,
            list(right_samples_map.keys()) + list(center_samples_map.keys()),
        )
        left_record["polarization"] = "left"

        right_record = MikelimaDwellPQWriter.extract_sample_type(
            record,
            right_samples_map,
            list(left_samples_map.keys()) + list(center_samples_map.keys()),
        )
        right_record["polarization"] = "right"

        self.sample_writer_inner.add_record(left_record,
                                            dwell_key=dwell_key_left)
        self.sample_writer_inner.add_record(right_record,
                                            dwell_key=dwell_key_right)

        if "samples_i_center" in record:
            center_record = MikelimaDwellPQWriter.extract_sample_type(
                record,
                center_samples_map,
                list(left_samples_map.keys()) + list(right_samples_map.keys()),
            )
            center_record["polarization"] = "center"

            self.sample_writer_inner.add_record(center_record,
                                                dwell_key=dwell_key_center)

        self.record_count += 1

    def close(self):
        if self._closed:
            return

        self.sample_writer_inner.close()

        self._closed = True

    @property
    def metadata(self) -> dict:
        return {
            "output": str(self._filename),
            "options": self._options,
            "batch_size": self.batch_size
        }
