from typing import Optional

from src.gui.gui import GUIEvents
from src.modules.moduleBase import ModuleBase
from src.modules.robot.wheelsController import WheelsController


class RobotModule(ModuleBase):
    class __Direction:
        FORWARD = 0
        BACKWARD = 1
        LEFT = 2
        RIGHT = 3

    def __init__(self, gui_events: GUIEvents):
        super().__init__(gui_events)

        self.__wheels = WheelsController()
        self.__current_direction: Optional[int] = None
        self.__next_direction: Optional[int] = None

        self._gui_events.robot_view_init.emit({
            "onForward": lambda enable: self.__handle_direction_change(RobotModule.__Direction.FORWARD, enable),
            "onBackward": lambda enable: self.__handle_direction_change(RobotModule.__Direction.BACKWARD, enable),
            "onTurnLeft": lambda enable: self.__handle_direction_change(RobotModule.__Direction.LEFT, enable),
            "onTurnRight": lambda enable: self.__handle_direction_change(RobotModule.__Direction.RIGHT, enable)
        })

    def close(self):
        self._gui_events.robot_view_hide.emit()
        super().close()

    def __handle_direction_change(self, direction: int, enable: bool):
        if not enable:
            if direction == self.__current_direction:
                self.__handle_release()
            else:
                self.__next_direction = None
            return

        if self.__current_direction is not None:
            self.__next_direction = direction
            return

        self.__current_direction = direction

        if direction == RobotModule.__Direction.FORWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
        elif direction == RobotModule.__Direction.BACKWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
        elif direction == RobotModule.__Direction.RIGHT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
        elif direction == RobotModule.__Direction.LEFT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
        else:
            raise ValueError("Invalid direction")

    def __handle_release(self):
        self.__current_direction = None
        if self.__next_direction is not None:
            next_direction = self.__next_direction
            self.__next_direction = None
            self.__handle_direction_change(next_direction, True)
            return
        self.__wheels.stop_wheels()
