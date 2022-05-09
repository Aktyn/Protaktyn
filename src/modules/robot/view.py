import numpy as np

from typing import Callable, Optional
from src.gui.core.button import Button
from src.gui.core.gui import GUI
from src.gui.core.gui_consts import GUIConsts
from src.gui.core.image import Image
from src.gui.core.label import Label
from src.gui.core.widget import Widget
from src.gui.views.view_base import ViewBase
from src.object_detection.objectDetector import Detection


class RobotView(ViewBase):
    def __init__(self, on_forward: Callable[[bool], any], on_backward: Callable[[bool], any],
                 on_turn_left: Callable[[bool], any], on_turn_right: Callable[[bool], any]):
        self.__on_forward = on_forward
        self.__on_backward = on_backward
        self.__on_turn_left = on_turn_left
        self.__on_turn_right = on_turn_right
        self.__gui: Optional[GUI] = None
        self.__detection_widgets: list[Widget] = []

        # ↑↓↶↷
        self.__button_forward = Button(text='Forward', pos=(0, 0), font_size=1,
                                       on_mouse_down=lambda: self.__on_forward(True),
                                       on_mouse_up=lambda: self.__on_forward(False))
        self.__button_backward = Button(text='Backward', pos=(0, 0), font_size=1,
                                        on_mouse_down=lambda: self.__on_backward(True),
                                        on_mouse_up=lambda: self.__on_backward(False))
        self.__button_turn_left = Button(text='Turn left', pos=(0, 0), font_size=1, background_color=(136, 150, 0),
                                         on_mouse_down=lambda: self.__on_turn_left(True),
                                         on_mouse_up=lambda: self.__on_turn_left(False))
        self.__button_turn_right = Button(text='Turn right', pos=(0, 0), font_size=1, background_color=(136, 150, 0),
                                          on_mouse_down=lambda: self.__on_turn_right(True),
                                          on_mouse_up=lambda: self.__on_turn_right(False))

        self.__depth_estimation_image = Image(pos=(0, GUI.DEFAULT_SIZE[1]), size=GUI.DEFAULT_SIZE)

    def load(self, gui: GUI):
        self.__gui = gui
        gui.set_size(GUI.DEFAULT_SIZE)
        width, height = GUI.DEFAULT_SIZE

        btn_size = height // 3

        self.__button_forward.set_pos((width // 2, btn_size // 2))
        self.__button_backward.set_pos((width // 2, height - btn_size // 2))
        self.__button_turn_left.set_pos((width // 2 - btn_size, height // 2))
        self.__button_turn_right.set_pos((width // 2 + btn_size, height // 2))

        for button in [self.__button_forward, self.__button_backward, self.__button_turn_left,
                       self.__button_turn_right]:
            button.set_size((int(btn_size * 1.618), btn_size))
            button.set_border_width(4)

        gui.add_widgets((self.__button_forward,
                        self.__button_backward,
                        self.__button_turn_left,
                        self.__button_turn_right))

    def toggle_fill_buttons(self, fill: bool):
        for button in [self.__button_forward, self.__button_backward, self.__button_turn_left,
                       self.__button_turn_right]:
            button.set_fill(fill)
        self.__gui.redraw()

    def toggle_depth_preview(self, show: bool):
        if show:
            self.__gui.set_size((GUI.DEFAULT_SIZE[0], GUI.DEFAULT_SIZE[1] * 2))
            self.__gui.add_widgets((self.__depth_estimation_image,))
        else:
            self.__gui.set_size(GUI.DEFAULT_SIZE)
            self.__gui.remove_widgets(self.__depth_estimation_image)

    def set_depth_estimation_image(self, image: np.ndarray):
        self.__depth_estimation_image.set_image(image)

    def set_steering_button_active(self, name: str, is_active: bool):
        button = self.__button_forward if name == 'forward' else self.__button_backward if name == 'backward' else self.__button_turn_left if name == 'left' else self.__button_turn_right if name == 'right' else None
        if button is not None:
            button.set_text_color((132, 199, 129) if is_active else (255, 255, 255))
            self.__gui.redraw()

    def set_detections(self, detections: list[Detection]):
        for widget in self.__detection_widgets:
            self.__gui.remove_widgets(widget)

        for detection in detections:
            # Draw bounding_box
            start_point = detection.bounding_box.left, detection.bounding_box.top
            end_point = detection.bounding_box.right, detection.bounding_box.bottom
            center = (int((start_point[0] + end_point[0]) / 2), int((start_point[1] + end_point[1]) / 2))
            color = (64, 64, 255)

            rect = Button(text='',
                          pos=center,
                          background_color=color)
            rect.set_size((int(end_point[0] - start_point[0]), int(end_point[1] - start_point[1])))
            rect.set_fill(False)
            rect.set_border_width(1)
            rect.set_disabled(True)
            self.__detection_widgets.append(rect)

            # Draw center point
            center = Button(text='', pos=center, background_color=color)
            center.set_size((2, 2))
            center.set_disabled(True)
            self.__detection_widgets.append(center)

            # Draw label and score
            category = detection.categories[0]
            class_name = category.label
            probability = round(category.score, 2)
            result_text = class_name + ' (' + str(probability) + ')'

            margin = 10  # pixels
            row_size = 10  # pixels
            label = Label(text=result_text,
                          pos=(int(margin + detection.bounding_box.left),
                               int(margin + row_size + detection.bounding_box.top)),
                          font_size=0.5,
                          font_thickness=1,
                          text_color=color,
                          align=GUIConsts.TextAlign.LEFT)
            self.__detection_widgets.append(label)

            self.__gui.add_widgets((rect, center, label))
        self.__gui.redraw()
