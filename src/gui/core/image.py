import numpy as np
import cv2

from src.gui.core.widget import Widget


class Image(Widget):
    def __init__(self, pos: tuple[int, int], size: tuple[int, int], fill=(0, 0, 0)):
        super().__init__(pos, size)
        self.__img = np.full(shape=(self._size[1], self._size[0], 3), fill_value=fill,
                             dtype=np.uint8)
        self.__base = self.__img.copy()

    def set_image(self, image: np.ndarray):
        height, width = image.shape[:2]
        if height != self._size[1] or width != self._size[0]:
            raise ValueError("Image size does not match widget size")
        self.__img = image

    def set_angle(self, angle: float):
        (cX, cY) = (self._size[0] // 2, self._size[1] // 2)
        m = cv2.getRotationMatrix2D((cX, cY), angle * 180, 1.0)

        (h, w) = self.__base.shape[:2]
        self.__img = cv2.warpAffine(self.__base, m, (w, h))
        # self.__img = cv2.rotate(self.__base)

    def draw(self, image: np.ndarray):
        height, width = self.__img.shape[:2]
        image_height, image_width = image.shape[:2]

        top = self._pos[1]
        bottom = self._pos[1] + height
        crop_top = 0
        crop_bottom = 0
        if top < 0:
            crop_top = -top
            top = 0
        if bottom > image_height:
            crop_bottom = bottom - image_height
            bottom = image_height

        left = self._pos[0]
        right = self._pos[0] + width
        crop_left = 0
        crop_right = 0
        if left < 0:
            crop_left = -left
            left = 0
        if right > image_width:
            crop_right = right - image_width
            right = image_width

        if bottom - top > 0 and right - left > 0:
            image[top:bottom, left:right] = self.__img[
                                            min(height, crop_top):max(0, height - crop_bottom),
                                            min(width, crop_left):max(0, width - crop_right)
                                            ]
