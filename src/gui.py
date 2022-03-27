from PyQt5 import QtWidgets, QtCore

import sys

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
BUTTON_WIDTH = 100
BUTTON_HEIGHT = 30

FULL_SCREEN = True  # Set to True to run on production


class GUIEvents(QtCore.QThread):
    set_label_text = QtCore.pyqtSignal(str)

    def __init__(self, on_init):
        QtCore.QThread.__init__(self)
        self.__on_init = on_init

    def run(self):
        self.__on_init(self)


class GUI:
    def __init__(self, on_init):
        app = QtWidgets.QApplication(sys.argv)
        width = app.primaryScreen().size().width() if FULL_SCREEN else WINDOW_WIDTH
        height = app.primaryScreen().size().height() if FULL_SCREEN else WINDOW_HEIGHT

        self.__window = QtWidgets.QMainWindow()
        self.__window.setWindowTitle("Protaktyn")

        self.__label = QtWidgets.QLabel(self.__window)
        self.__label.setText("-")
        offset = 8
        self.__label.move(offset, offset)
        self.__label.setFixedWidth(width - offset * 2)
        self.__label.setFixedHeight(height - offset * 2)
        self.__label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        close_button = QtWidgets.QPushButton(self.__window)
        close_button.setText("Close")
        close_button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        close_button.move((width - BUTTON_WIDTH) / 2, height - BUTTON_HEIGHT - 16)
        close_button.clicked.connect(QtWidgets.qApp.quit)

        if FULL_SCREEN:
            self.__window.showFullScreen()
        else:
            self.__window.setGeometry((width - WINDOW_WIDTH) / 2, (height - WINDOW_HEIGHT) / 2,
                                      WINDOW_WIDTH, WINDOW_HEIGHT)
            self.__window.show()

        downloader = GUIEvents(on_init)
        downloader.set_label_text.connect(lambda text: self.__label.setText(text))
        downloader.start()

        exec_code = app.exec_()
        downloader.terminate()
        sys.exit(exec_code)
