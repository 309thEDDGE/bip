from pathlib import Path
from typing import Protocol, runtime_checkable

import pyarrow as pa


@runtime_checkable
class Recorder(Protocol):
    def __init__(self,
                 filename: Path,
                 schema: pa.Schema,
                 options: dict = {}
                 ):
        """
        Records packets.
        """
        pass

    @staticmethod
    def extension() -> str:
        """
        The file extention type for files that this recorder writes.
        """
        pass

    @property
    def metadata(self) -> dict:
        """
        Metadata about this recorder.
        """
        pass

    def add_record(self, record: dict):
        """
        Add a record to the recorder, to be written to the output.
        """
        pass

    def close(self):
        """
        Close the recorder.
        """
        pass
