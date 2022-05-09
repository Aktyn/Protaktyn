import cv2
import numpy as np
from src.gui.core.widget import Widget


class Circle(Widget):
    def __init__(self, pos=(0, 0), radius=64, background_color=(0, 0, 0)):
        super().__init__(pos)
        self.__background_color = background_color
        self.__radius = radius

    def draw(self, image: np.ndarray):
        cv2.circle(image, self._pos, self.__radius, self.__background_color, cv2.FILLED, cv2.LINE_AA)
