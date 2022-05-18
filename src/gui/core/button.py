import numpy as np
import cv2

from typing import Callable
from src.gui.core.gui_consts import GUIConsts
from src.gui.core.label import Label


class Button(Label):
    __BG_COLOR = (154, 166, 38)
    __HOVER_COLOR = (172, 182, 77)

    def __init__(self, text: str, pos: tuple[int, int], padding=16, font_size: float = 2, font_thickness=2,
                 font_color=(255, 255, 255), background_color=__BG_COLOR, on_click: Callable[['Button'], None] = None,
                 on_mouse_up: Callable = None,
                 on_mouse_down: Callable = None):
        super().__init__(text, pos, font_size, font_thickness, font_color, GUIConsts.TextAlign.CENTER)
        self.__padding = padding
        self.__on_click = on_click
        self.__on_mouse_up = on_mouse_up
        self.__on_mouse_down = on_mouse_down
        self.__background_color = background_color
        self.__disabled = False

        self.__border_width = 1
        self.__fill = True
        self.__hover = False

    def click(self):
        if self.__on_click:
            self.__on_click(self)

    def on_mouse_up(self):
        if self.__on_mouse_up:
            self.__on_mouse_up()

    def on_mouse_down(self):
        if self.__on_mouse_down:
            self.__on_mouse_down()

    def is_hover(self):
        return self.__hover

    def set_disabled(self, disabled: bool):
        self.__disabled = disabled

    def is_disabled(self):
        return self.__disabled

    def aabb(self):
        (w, h), baseline = self._measurements
        if self._size is None:
            left_top = (self._pos[0] - w // 2 - self.__padding, self._pos[1] - h // 2 - self.__padding)
            right_bottom = (self._pos[0] + w // 2 + self.__padding, self._pos[1] + h // 2 + self.__padding)
            return left_top, right_bottom
        else:
            left_top = (self._pos[0] - self._size[0] // 2, self._pos[1] - self._size[1] // 2)
            right_bottom = (self._pos[0] + self._size[0] // 2, self._pos[1] + self._size[1] // 2)
            return left_top, right_bottom

    def draw(self, image: np.ndarray):
        left_top, right_bottom = self.aabb()
        cv2.rectangle(image, left_top, right_bottom,
                      color=Button.__HOVER_COLOR if self.__hover else self.__background_color,
                      thickness=(-1 if self.__fill else self.__border_width))
        super().draw(image)

    def is_point_inside(self, x: int, y: int):
        left_top, right_bottom = self.aabb()
        return left_top[0] <= x <= right_bottom[0] and left_top[1] <= y <= right_bottom[1]

    def toggle_hover(self, enable: bool):
        if enable == self.__hover:
            return False
        self.__hover = enable

        return True

    def set_border_width(self, width: int):
        self.__border_width = width

    def set_fill(self, fill: bool):
        self.__fill = fill
