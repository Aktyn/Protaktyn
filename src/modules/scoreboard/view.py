from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow

from src.gui.gui_consts import GUIConsts
from src.utils import show_gui

if not show_gui():
    from src.gui.gui_utils import MockPyQtSignal


    class MockScoreboardViewEvents:
        scoreboard_view_update_points = MockPyQtSignal()
        scoreboard_view_hide = MockPyQtSignal()


class ScoreboardViewEvents:
    scoreboard_view_update_points = QtCore.pyqtSignal(int, int)
    scoreboard_view_hide = QtCore.pyqtSignal()


class ScoreboardView:
    def __init__(self, window: QMainWindow, events: ScoreboardViewEvents):
        self.__window = window
        self.__is_view_active = False

        events.scoreboard_view_update_points.connect(lambda p1, p2: self.__handle_update_points(p1, p2))
        events.scoreboard_view_hide.connect(self.__handle_view_hide)

    def __init_view(self):
        self.__points_label = QtWidgets.QLabel(self.__window)
        self.__points_label.move(0, GUIConsts.TOP_BAR_HEIGHT)
        self.__points_label.setFixedWidth(self.__window.width())
        self.__points_label.setFixedHeight(self.__window.height() - GUIConsts.TOP_BAR_HEIGHT)
        self.__points_label.setAlignment(QtCore.Qt.AlignCenter)
        self.__points_label.setFont(QFont(None, 72))
        self.__points_label.font().setBold(True)
        self.__points_label.setText("- | -")

        self.__points_label.show()

        self.__is_view_active = True

    def __handle_view_hide(self):
        self.__points_label.hide()
        self.__points_label.destroy(destroyWindow=True, destroySubWindows=True)
        self.__window.repaint()
        self.__is_view_active = False

    def __handle_update_points(self, p1: int, p2: int):
        if not self.__is_view_active:
            self.__init_view()
        self.__points_label.setText(f"{p1} | {p2}")
