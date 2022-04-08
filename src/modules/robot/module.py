from typing import Optional

from src.config.commands import Commands
from src.gui.gui import GUIEvents
from src.modules.moduleBase import ModuleBase
from src.modules.robot.wheelsController import WheelsController
from src.object_detection.objectDetector import ObjectDetector
from src.utils import loud_print


class RobotModule(ModuleBase):
    class __Direction:
        FORWARD = 0
        BACKWARD = 1
        LEFT = 2
        RIGHT = 3

    def __init__(self, gui_events: GUIEvents):
        super().__init__(gui_events)

        self.__detector: Optional[ObjectDetector] = None
        self.__wheels = WheelsController()
        self.__current_direction: Optional[int] = None
        self.__next_direction: Optional[int] = None

        self._gui_events.robot_view_init.emit({
            "onForward": lambda enable: self.__handle_direction_change(RobotModule.__Direction.FORWARD, enable),
            "onBackward": lambda enable: self.__handle_direction_change(RobotModule.__Direction.BACKWARD, enable),
            "onTurnLeft": lambda enable: self.__handle_direction_change(RobotModule.__Direction.LEFT, enable),
            "onTurnRight": lambda enable: self.__handle_direction_change(RobotModule.__Direction.RIGHT, enable)
        })

        super().register_command(Commands.ROBOT.target_cat, lambda *args: self.__start_targeting_object('cat'))

        # TEMP!!!
        self.__start_targeting_object('cat')

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
            self._gui_events.robot_view_set_steering_button_active.emit('forward', True)
        elif direction == RobotModule.__Direction.BACKWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self._gui_events.robot_view_set_steering_button_active.emit('backward', True)
        elif direction == RobotModule.__Direction.RIGHT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
            self._gui_events.robot_view_set_steering_button_active.emit('right', True)
        elif direction == RobotModule.__Direction.LEFT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self._gui_events.robot_view_set_steering_button_active.emit('left', True)
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
        for button_name in ['forward', 'backward', 'left', 'right']:
            self._gui_events.robot_view_set_steering_button_active.emit(button_name, False)

    def __start_targeting_object(self, object_name: str):
        if self.__detector is not None:
            print("There is already a detector running")
            return
        loud_print(f"Starting targeting object: {object_name}", True)
        # self.__detector = ObjectDetector()
        # self.__detector.run(object_name)
