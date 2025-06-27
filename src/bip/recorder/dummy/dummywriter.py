from pathlib import Path

import pyarrow as pa


class DummyWriter:
    @staticmethod
    def extension() -> str:
        return "dummy"

    def __init__(self,
                 filename: Path,
                 schema: pa.schema,
                 options: dict = None,
                 batch_size: int = 1000
                 ):

        if options is None:
            options = {}

        self._closed = False

        self._filename = filename
        self._schema = schema
        self._options = options

        self._add_record = self._options.get("add_record_callback", None)
        self._close = self._options.get("close_callback", None)

        self.batch_size = batch_size
        self.schema = schema
        self.data = []
        self.writer = None

        self.current_index = 0

    def _record(self):
        """
        The point of the dummy writer is that it doesn't record anything.
        """
        pass

    def add_record(self, record: dict):
        if self._add_record is not None:
            self._add_record(record)

    def close(self):
        if self._closed:
            return

        if self.current_index != 0:
            self._record()

        if self._close is not None:
            self._close()

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
