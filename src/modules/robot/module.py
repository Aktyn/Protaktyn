import random
from datetime import datetime
from enum import Enum
from threading import Thread
from typing import Optional, Tuple

from src.config.commands import Commands
from src.gui.gui import GUIEvents
from src.modules.moduleBase import ModuleBase
from src.modules.robot.wheelsController import WheelsController
from src.object_detection.objectDetector import ObjectDetector
from src.utils import loud_print


class RobotModule(ModuleBase):
    class __Direction(Enum):
        FORWARD, BACKWARD, LEFT, RIGHT = range(4)

    def __init__(self, gui_events: GUIEvents):
        super().__init__(gui_events)

        self.__detector: Optional[ObjectDetector] = None
        self.__movement_thread: Optional[Thread] = None
        self.__last_target_detection: Optional[dict] = None

        self.__wheels = WheelsController()
        self.__current_direction: Optional[RobotModule.__Direction] = None
        self.__next_direction: Optional[RobotModule.__Direction] = None

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
        if self.__detector is not None:
            self.__detector.stop()
        super().close()

    def __handle_direction_change(self, direction: __Direction, enable: bool, force=False):
        if not enable:
            if direction == self.__current_direction:
                self.__handle_release()
            else:
                self.__next_direction = None
            return

        if self.__current_direction is not None and not force:
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

    def __smart_movement_thread(self):
        if self.__detector is None:
            return
        detector_id = self.__detector.id()

        idle_time = 30.0
        rotation_interval = 15.0
        rotation_duration = random.uniform(0.2, 1)  # must not be larger than rotation_interval
        rotation_direction = random.choice([-1, 1])
        max_rotation_duration_towards_target = 0.5
        moving_towards_target_duration = 0.5  # TODO: it can be adjusted according to recognition result rect area

        last_rotation_timestamp = 0
        is_looking_for_target = False
        is_rotating_toward_target = False
        is_following_target = False

        while self.__detector and self.__detector.id() == detector_id:
            now = datetime.now().timestamp()

            last_target_detection_timestamp = self.__last_target_detection['timestamp']

            # If there is no target detected for given amount of time
            if self.__last_target_detection is None or now - last_target_detection_timestamp > idle_time:
                if now - last_rotation_timestamp > rotation_interval:
                    last_rotation_timestamp = now
                    rotation_duration = random.uniform(0.2, 1)
                    rotation_direction = random.choice([-1, 1])
                elif now - last_rotation_timestamp < rotation_duration:
                    if not is_looking_for_target:
                        if rotation_direction == 1:
                            self.__handle_direction_change(RobotModule.__Direction.LEFT, True, True)
                        else:
                            self.__handle_direction_change(RobotModule.__Direction.RIGHT, True, True)
                        is_looking_for_target = True
                elif is_looking_for_target:
                    self.__handle_release()
                    is_looking_for_target = False
            # React to detected target position by turning robot towards it
            else:
                target_position_x = self.__last_target_detection['position'][0]
                rotation_duration_towards_target = abs(target_position_x) * max_rotation_duration_towards_target

                # Rotate slightly towards target
                if now - last_target_detection_timestamp < rotation_duration_towards_target:
                    if not is_rotating_toward_target:
                        direction = -1 if target_position_x > 0.0 else 1
                        if direction == 1:
                            self.__handle_direction_change(RobotModule.__Direction.LEFT, True, True)
                        else:
                            self.__handle_direction_change(RobotModule.__Direction.RIGHT, True, True)
                        is_rotating_toward_target = True
                # Move towards target
                elif now - last_target_detection_timestamp < moving_towards_target_duration + rotation_duration_towards_target:
                    is_rotating_toward_target = False
                    if not is_following_target:
                        self.__handle_direction_change(RobotModule.__Direction.FORWARD, True, True)
                        is_following_target = True
                elif is_following_target:
                    self.__handle_release()
                    is_following_target = False

    def __handle_target_detection(self, position: Tuple[float, float]):
        print("Target detected at position:", position)

        self.__last_target_detection = {
            'position': position,
            'timestamp': datetime.now().timestamp()
        }

    def __start_targeting_object(self, object_name: str):
        if self.__detector is not None:
            print("There is already a detector running")
            return
        loud_print(f"Starting targeting object: {object_name}", True)
        self.__detector = ObjectDetector(self.__handle_target_detection)
        self.__detector.run(object_name)

        if self.__movement_thread is not None:
            self.__movement_thread = Thread(target=self.__smart_movement_thread)
            self.__movement_thread.daemon = True
