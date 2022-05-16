import cv2
import numpy as np

from src.gui.core.widget import Widget


class Line(Widget):
    def __init__(self, pos_start=(0, 0), pos_end=(0, 0), color=(0, 0, 0), thickness=1):
        super().__init__(pos_start)
        self.__pos_end = pos_end
        self.__color = color
        self.__thickness = thickness

    def set_color(self, color: tuple[int, int, int]):
        self.__color = color

    def set_points(self, pos_start: tuple[int, int], pos_end: tuple[int, int]):
        self._pos = pos_start
        self.__pos_end = pos_end

    def draw(self, image: np.ndarray):
        cv2.line(image, self._pos, self.__pos_end, self.__color, thickness=self.__thickness, lineType=cv2.LINE_AA)
