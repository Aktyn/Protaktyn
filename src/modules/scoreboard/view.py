from typing import Callable, Optional
from src.gui.core.button import Button
from src.gui.core.label import Label
from src.gui.core.gui import GUI
from src.gui.views.view_base import ViewBase


class ScoreboardView(ViewBase):
    def __init__(self, on_left_player_point: Callable, on_right_player_point: Callable):
        self.__on_left_player_point = on_left_player_point
        self.__on_right_player_point = on_right_player_point
        self.__gui: Optional[GUI] = None

        # TODO: left and right align for point labels
        self.__left_points_label = Label(text='0', pos=(0, 0), font_size=6, font_thickness=3)
        self.__right_points_label = Label(text='0', pos=(0, 0), font_size=6, font_thickness=3)

        self.__left_set_points_label = Label(text='0', pos=(0, 0), font_size=2, font_thickness=1)
        self.__right_set_points_label = Label(text='0', pos=(0, 0), font_size=2, font_thickness=1)

    def load(self, gui: GUI):
        self.__gui = gui
        gui.set_size(GUI.DEFAULT_SIZE)
        width, height = GUI.DEFAULT_SIZE

        self.__left_points_label.set_pos((width // 2 - 100, height // 2))
        self.__right_points_label.set_pos((width // 2 + 100, height // 2))

        self.__left_set_points_label.set_pos((width // 2 - 30, height - 42))
        self.__right_set_points_label.set_pos((width // 2 + 30, height - 42))

        gui.add_widgets((
            Button(text='Add point to left', pos=(width // 2 - 160, 40), padding=16,
                   on_click=self.__on_left_player_point, font_size=1),
            Button(text='Add point to right', pos=(width // 2 + 160, 40), padding=16,
                   on_click=self.__on_right_player_point, font_size=1),

            self.__left_points_label,
            Label(text='|', pos=(width // 2, height // 2), font_size=6, font_thickness=3),  # Points separator
            self.__right_points_label,

            self.__left_set_points_label,
            Label(text='|', pos=(width // 2, height - 42), font_size=2, font_thickness=1),  # Set points separator
            self.__right_set_points_label
        ))

    def update_points(self, left_player_points: int, right_player_points: int):
        self.__left_points_label.set_text(str(left_player_points))
        self.__right_points_label.set_text(str(right_player_points))
        self.__gui.redraw()

    def update_set_points(self, left_player_set_points: int, right_player_set_points: int):
        self.__left_set_points_label.set_text(str(left_player_set_points))
        self.__right_set_points_label.set_text(str(right_player_set_points))
        self.__gui.redraw()
