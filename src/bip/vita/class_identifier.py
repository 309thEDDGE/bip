import numpy as np


class ClassIdentifier:
    def __init__(self, class_id: np.ndarray):
        assert (len(class_id) == 2)
        self._data = class_id

    @property
    def pad_bit_count(self) -> int:
        return self._data[0] >> 27

    @property
    def oui(self) -> int:
        return self._data[0] & 0xFFFFFF

    @property
    def information_class_code(self) -> int:
        return self._data[1] >> 16

    @property
    def packet_class_code(self) -> int:
        return self._data[1] & 0xFFFF
