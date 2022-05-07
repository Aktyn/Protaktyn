import numpy as np
from abc import abstractmethod
from typing import Optional


class Widget:
    def __init__(self, pos: tuple[int, int], size: Optional[tuple[int, int]] = None):
        self._pos = pos
        self._size = size

    def set_pos(self, pos: tuple[int, int]):
        self._pos = pos

    def set_size(self, size: tuple[int, int]):
        self._size = size

    @abstractmethod
    def draw(self, image: np.ndarray):
        pass
