from pathlib import Path
from typing import Protocol, runtime_checkable

import pyarrow as pa


@runtime_checkable
class Recorder(Protocol):
    def __init__(
        self,
        filename: Path,
        schema: pa.Schema = None,
        options: dict = None
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

    def add_record(self, record: dict, dwell_key: int = None):
        """
        Add a record to this recorder.
        """
        pass

    def close(self):
        """
        Close the recorder.
        """
        pass
