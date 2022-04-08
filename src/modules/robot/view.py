from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow

from src.gui.gui_consts import GUIConsts
from src.utils import show_gui

if not show_gui():
    from src.gui.gui_utils import MockPyQtSignal


    class MockRobotViewEvents:
        robot_view_init = MockPyQtSignal()
        robot_view_hide = MockPyQtSignal()


class RobotViewEvents:
    robot_view_init = QtCore.pyqtSignal(dict)
    robot_view_hide = QtCore.pyqtSignal()
    robot_view_set_steering_button_active = QtCore.pyqtSignal(str, bool)


class ButtonEx(QtWidgets.QPushButton):
    pressed = QtCore.pyqtSignal()
    released = QtCore.pyqtSignal()

    def __init__(self, window: QMainWindow):
        super().__init__(window)

    def mousePressEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.pressed.emit()

    def mouseReleaseEvent(self, event):
        self.released.emit()


class RobotView:
    def __init__(self, window: QMainWindow, events: RobotViewEvents):
        self.__window = window
        self.__is_view_active = False

        events.robot_view_init.connect(lambda _: self.__init_view(_))
        events.robot_view_hide.connect(lambda: self.__handle_view_hide())
        events.robot_view_set_steering_button_active.connect(self.__set_steering_button_active)

    def __init_view(self, steering_events: dict):
        if self.__is_view_active:
            return

        width = int(self.__window.width() / 3)
        height = int((self.__window.height() - GUIConsts.TOP_BAR_HEIGHT) / 3)

        # TODO: circular joystick controls
        self.__control_buttons = dict({
            'forward': ButtonEx(self.__window),
            'backward': ButtonEx(self.__window),
            'left': ButtonEx(self.__window),
            'right': ButtonEx(self.__window),
        })

        self.__control_buttons['forward'].setText('↑')
        self.__control_buttons['forward'].move(width, GUIConsts.TOP_BAR_HEIGHT)
        self.__control_buttons['forward'].pressed.connect(lambda: steering_events['onForward'](True))
        self.__control_buttons['forward'].released.connect(lambda: steering_events['onForward'](False))

        self.__control_buttons['backward'].setText('↓')
        self.__control_buttons['backward'].move(width, GUIConsts.TOP_BAR_HEIGHT + height)
        self.__control_buttons['backward'].pressed.connect(lambda: steering_events['onBackward'](True))
        self.__control_buttons['backward'].released.connect(lambda: steering_events['onBackward'](False))

        self.__control_buttons['left'].setText('↶')
        self.__control_buttons['left'].move(0, GUIConsts.TOP_BAR_HEIGHT + height)
        self.__control_buttons['left'].pressed.connect(lambda: steering_events['onTurnLeft'](True))
        self.__control_buttons['left'].released.connect(lambda: steering_events['onTurnLeft'](False))

        self.__control_buttons['right'].setText('↷')
        self.__control_buttons['right'].move(width * 2, GUIConsts.TOP_BAR_HEIGHT + height)
        self.__control_buttons['right'].pressed.connect(lambda: steering_events['onTurnRight'](True))
        self.__control_buttons['right'].released.connect(lambda: steering_events['onTurnRight'](False))

        for btn in self.__control_buttons.values():
            btn.setFixedWidth(width)
            btn.setFixedHeight(height)
            # btn.setAlignment(QtCore.Qt.AlignCenter)
            btn.setFont(QFont(None, 72))
            btn.font().setBold(True)
            btn.setStyleSheet('color: #fff')
            btn.show()

        self.__is_view_active = True

    def __handle_view_hide(self):
        for btn in self.__control_buttons.values():
            btn.hide()
            btn.destroy(destroyWindow=True, destroySubWindows=True)
        self.__window.repaint()
        self.__is_view_active = False

    def __set_steering_button_active(self, btn_name: str, is_active: bool):
        self.__control_buttons[btn_name].setStyleSheet(f'color: {"#81C784" if is_active else "#fff"}')
