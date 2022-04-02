from typing import Callable

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow

from src.gui.gui_consts import GUIConsts
from src.utils import show_gui

if not show_gui():
    from src.gui.gui_utils import MockPyQtSignal


    class MockScoreboardViewEvents:
        scoreboard_view_init = MockPyQtSignal()
        scoreboard_view_hide = MockPyQtSignal()
        scoreboard_view_update_points = MockPyQtSignal()
        scoreboard_view_update_set_points = MockPyQtSignal()


class ScoreboardViewEvents:
    scoreboard_view_init = QtCore.pyqtSignal(dict)
    scoreboard_view_hide = QtCore.pyqtSignal()
    scoreboard_view_update_points = QtCore.pyqtSignal(int, int)
    scoreboard_view_update_set_points = QtCore.pyqtSignal(int, int)


class PointsLabel(QtWidgets.QLabel):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        super().setAlignment(QtCore.Qt.AlignCenter)


class ScoreboardView:
    def __init__(self, window: QMainWindow, events: ScoreboardViewEvents):
        self.__window = window
        self.__is_view_active = False

        events.scoreboard_view_init.connect(self.__init_view)
        events.scoreboard_view_hide.connect(self.__handle_view_hide)
        events.scoreboard_view_update_points.connect(lambda p1, p2: self.__handle_update_points(p1, p2))
        events.scoreboard_view_update_set_points.connect(lambda p1, p2: self.__handle_update_set_points(p1, p2))

    def __init_view(self, point_increase_events: dict):
        self.__points_label = PointsLabel(self.__window)
        self.__points_label.move(0, GUIConsts.TOP_BAR_HEIGHT)
        self.__points_label.setFixedWidth(self.__window.width())
        self.__points_label.setFixedHeight(self.__window.height() - GUIConsts.TOP_BAR_HEIGHT)
        self.__points_label.setFont(QFont(None, 72))
        self.__points_label.font().setBold(True)
        self.__points_label.show()

        set_points_label_height = 100
        self.__set_points_label = PointsLabel(self.__window)
        self.__set_points_label.move(0, self.__window.height() - set_points_label_height)
        self.__set_points_label.setFixedWidth(self.__window.width())
        self.__set_points_label.setFixedHeight(set_points_label_height)
        self.__set_points_label.setFont(QFont(None, 48))
        self.__set_points_label.font().setBold(True)
        self.__set_points_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        self.__set_points_label.show()

        btn_height = 64

        self.__left_player_point_btn = QtWidgets.QPushButton(self.__window)
        self.__left_player_point_btn.move(0, GUIConsts.TOP_BAR_HEIGHT)
        self.__left_player_point_btn.setText("Add point to left")
        self.__left_player_point_btn.clicked.connect(lambda: point_increase_events["on_left_player_point"]())

        self.__right_player_point_btn = QtWidgets.QPushButton(self.__window)
        self.__right_player_point_btn.move(self.__window.width() // 2, GUIConsts.TOP_BAR_HEIGHT)
        self.__right_player_point_btn.setText("Add point to right")
        self.__right_player_point_btn.clicked.connect(lambda: point_increase_events["on_right_player_point"]())

        for btn in [self.__left_player_point_btn, self.__right_player_point_btn]:
            btn.setFixedWidth(self.__window.width() // 2)
            btn.setFixedHeight(btn_height)
            btn.setFont(QFont(None, 24))
            btn.font().setBold(True)
            btn.show()

        self.__is_view_active = True

    def __handle_view_hide(self):
        self.__points_label.hide()
        self.__points_label.destroy(destroyWindow=True, destroySubWindows=True)
        self.__window.repaint()
        self.__is_view_active = False

    def __handle_update_points(self, p1: int, p2: int):
        if not self.__is_view_active:
            return
        self.__points_label.setText(f"{p1 if p1 >= 10 else ' ' + str(p1)} | {p2 if p2 >= 10 else str(p2) + ' '}")

    def __handle_update_set_points(self, p1: int, p2: int):
        if not self.__is_view_active:
            return
        self.__set_points_label.setText(f"{p1} | {p2}")
