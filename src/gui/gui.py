from typing import Callable
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont

from src.gui.gui_consts import GUIConsts
from src.gui.scoreboardView import ScoreboardViewEvents, ScoreboardView

import sys


class GUIEvents(QtCore.QThread, ScoreboardViewEvents):
    close = QtCore.pyqtSignal()
    show_confirmation_info = QtCore.pyqtSignal(str)
    close_confirmation_info = QtCore.pyqtSignal()
    set_info_text = QtCore.pyqtSignal(str)

    def __init__(self, on_init: Callable[[any], None]):
        QtCore.QThread.__init__(self)
        self.__on_init = on_init

    def run(self):
        self.__on_init(self)


class GUI:
    def __init__(self, on_init: Callable[[GUIEvents], None]):
        self.__app = QtWidgets.QApplication(sys.argv)
        width = self.__app.primaryScreen().size().width() if GUIConsts.FULL_SCREEN else GUIConsts.WINDOW_WIDTH
        height = self.__app.primaryScreen().size().height() if GUIConsts.FULL_SCREEN else GUIConsts.WINDOW_HEIGHT

        self.__window = QtWidgets.QMainWindow()
        self.__window.setWindowTitle("Protaktyn")
        self.__window.setStyleSheet(f"background-color: {GUIConsts.BACKGROUND_COLOR}; color: {GUIConsts.TEXT_COLOR}")
        self.__info_label = QtWidgets.QLabel(self.__window)
        self.__info_label.setText("-")
        offset = 8
        self.__info_label.move(GUIConsts.BUTTON_WIDTH + offset, 0)
        self.__info_label.setFixedWidth(width - GUIConsts.BUTTON_WIDTH - offset * 2)
        self.__info_label.setFixedHeight(GUIConsts.TOP_BAR_HEIGHT)
        self.__info_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        close_button = QtWidgets.QPushButton(self.__window)
        close_button.setText("Close")
        close_button.setFixedSize(GUIConsts.BUTTON_WIDTH, GUIConsts.TOP_BAR_HEIGHT)
        close_button.move(0, 0)
        close_button.clicked.connect(QtWidgets.qApp.quit)

        self.__events = GUIEvents(on_init)
        self.__events.show_confirmation_info.connect(lambda text: self.__handle_show_confirmation_info(text))
        self.__events.close_confirmation_info.connect(lambda: self.__confirmation_info_label.hide())
        self.__events.set_info_text.connect(lambda text: self.__info_label.setText(text))
        self.__events.close.connect(self.__quit)

        # Init views
        ScoreboardView(self.__window, self.__events)

        self.__events.start()

        if GUIConsts.FULL_SCREEN:
            self.__window.showFullScreen()
        else:
            self.__window.setGeometry((width - GUIConsts.WINDOW_WIDTH) / 2, (height - GUIConsts.WINDOW_HEIGHT) / 2,
                                      GUIConsts.WINDOW_WIDTH, GUIConsts.WINDOW_HEIGHT)
            self.__window.show()

        exec_code = self.__app.exec_()
        self.__events.terminate()
        sys.exit(exec_code)

    def __handle_show_confirmation_info(self, text):
        if not hasattr(self, "__confirmation_info_label"):
            self.__confirmation_info_label = QtWidgets.QLabel(self.__window)
            self.__confirmation_info_label.move(0, 0)
            self.__confirmation_info_label.setFixedWidth(self.__window.width())
            self.__confirmation_info_label.setFixedHeight(self.__window.height())
            self.__confirmation_info_label.setWordWrap(True)
            self.__confirmation_info_label.setFont(QFont(None, 32))
            self.__confirmation_info_label.setStyleSheet(f"background-color: {GUIConsts.BACKGROUND_COLOR}")

        self.__confirmation_info_label.setText(text)
        self.__confirmation_info_label.show()

    def __quit(self):
        self.__app.quit()
