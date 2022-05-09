import cv2
import numpy as np

from math import cos, sin, atan2, sqrt
from src.gui.core.widget import Widget


class Rect(Widget):
    def __init__(self, pos=(0, 0), size=(0, 0), background_color=(0, 0, 0)):
        super().__init__(pos, size)
        self.__background_color = background_color
        self.__angle = 0

    def set_angle(self, angle):
        self.__angle = angle

    def draw(self, image: np.ndarray):
        d = sqrt(self._size[1] ** 2 + self._size[0] ** 2) / 2.0
        beta = atan2(self._size[1], self._size[0])

        vertices = np.array([
            (int(self._pos[0] - d * cos(beta - self.__angle)), int(self._pos[1] - d * sin(beta - self.__angle))),
            (int(self._pos[0] - d * cos(beta + self.__angle)), int(self._pos[1] + d * sin(beta + self.__angle))),
            (int(self._pos[0] + d * cos(beta - self.__angle)), int(self._pos[1] + d * sin(beta - self.__angle))),
            (int(self._pos[0] + d * cos(beta + self.__angle)), int(self._pos[1] - d * sin(beta + self.__angle)))
        ], np.int32)
        cv2.fillConvexPoly(image, vertices, color=self.__background_color, lineType=cv2.LINE_AA)
