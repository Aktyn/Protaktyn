import numpy as np
import cv2

from typing import Optional
from src.gui.core.gui_consts import GUIConsts
from src.gui.core.widget import Widget


class Label(Widget):
    def __init__(self, text: str, pos: tuple[int, int], font_size: float = 4, font_thickness=2,
                 text_color=(241, 239, 236),
                 align: Optional[int] = GUIConsts.TextAlign.CENTER):
        super().__init__(pos)
        self.__text = text
        self.__font_size = font_size
        self.__font_thickness = font_thickness
        self.__text_color = text_color
        self.__align = align
        self._measurements = self.__measure()

    def __measure(self):
        return cv2.getTextSize(self.__text, cv2.FONT_HERSHEY_SIMPLEX, self.__font_size,
                               self.__font_thickness)

    def set_text(self, text: str):
        self.__text = text

    def get_text(self):
        return self.__text

    def set_font_size(self, size: float):
        self.__font_size = size
        self._measurements = self.__measure()

    def set_font_thickness(self, thickness: int):
        self.__font_thickness = thickness
        self._measurements = self.__measure()

    def set_text_color(self, color: tuple[int, int, int]):
        self.__text_color = color

    def draw(self, image: np.ndarray):
        (w, h), baseline = self._measurements
        off_x = ((w // 2) if self.__align & GUIConsts.TextAlign.H_CENTER else 0)
        off_y = ((h // 2) if self.__align & GUIConsts.TextAlign.V_CENTER else 0)
        cv2.putText(image, text=self.__text,
                    org=(self._pos[0] - off_x,
                         self._pos[1] + off_y),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=self.__font_size, color=self.__text_color, thickness=self.__font_thickness,
                    lineType=cv2.LINE_AA,
                    bottomLeftOrigin=False)
