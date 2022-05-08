import random
import time
from datetime import datetime
from enum import Enum
from threading import Thread
from typing import Optional

from src.config.commands import Commands
from src.depth_estimation.depth import DepthEstimator
from src.gui.core.gui import GUI
from src.modules.moduleBase import ModuleBase
from src.modules.robot.view import RobotView
from src.modules.robot.wheelsController import WheelsController
from src.object_detection.objectDetector import ObjectDetector, Detection
from src.common.utils import loud_print


class RobotModule(ModuleBase):
    class __Direction(Enum):
        FORWARD, BACKWARD, LEFT, RIGHT = range(4)

    def __init__(self, gui: GUI):
        super().__init__(gui)

        self.__view = RobotView(
            on_forward=lambda enable: self.__handle_direction_change(RobotModule.__Direction.FORWARD, enable),
            on_backward=lambda enable: self.__handle_direction_change(RobotModule.__Direction.BACKWARD, enable),
            on_turn_left=lambda enable: self.__handle_direction_change(RobotModule.__Direction.LEFT, enable),
            on_turn_right=lambda enable: self.__handle_direction_change(RobotModule.__Direction.RIGHT, enable)
        )
        self._gui.set_view(self.__view)

        self.__detector: Optional[ObjectDetector] = None
        self.__depth: Optional[DepthEstimator] = None
        self.__movement_thread: Optional[Thread] = None
        self.__last_target_detection: Optional[dict] = None

        self.__wheels = WheelsController()
        self.__current_direction: Optional[RobotModule.__Direction] = None
        self.__next_direction: Optional[RobotModule.__Direction] = None

        super().register_command(Commands.ROBOT.target_cat,  # , 'person'
                                 lambda *args: self.__start_targeting_objects('cat', 'dog', 'horse', 'sheep', 'cow',
                                                                              'bear', 'zebra', 'teddy bear', 'bottle'))

        self.__detector = ObjectDetector(self._gui)
        self.__depth = DepthEstimator(self._gui)

        self.__is_targeting = False
        self.__targeting_process: Optional[Thread] = None

        # TEMP
        # self.__start_targeting_object('cat')

    def close(self):
        self.stop_targeting()
        self.__wheels.close()
        self.__detector.close()
        self.__depth.close()
        super().close()

    def stop_targeting(self):
        self.__view.toggle_fill_buttons(True)
        self.__view.toggle_depth_preview(False)
        self._gui.stop_camera_preview()

        self.__is_targeting = False
        if self.__targeting_process is not None:
            self.__targeting_process.join()
            self.__targeting_process = None

        if self.__movement_thread is not None:
            self.__movement_thread.join()
            self.__movement_thread = None

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
            self.__view.set_steering_button_active('forward', True)
        elif direction == RobotModule.__Direction.BACKWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self.__view.set_steering_button_active('backward', True)
        elif direction == RobotModule.__Direction.RIGHT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
            self.__view.set_steering_button_active('right', True)
        elif direction == RobotModule.__Direction.LEFT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self.__view.set_steering_button_active('left', True)
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
            self.__view.set_steering_button_active(button_name, False)

    def __smart_movement_thread(self):
        print("Smart movement thread started")
        # if self.__detector is None:
        #     return
        # detector_id = self.__detector.id()

        next_action_delay = 3
        idle_time = 15.0
        rotation_interval = 8.0
        rotation_duration = 0
        randomize_rotation_direction = True
        rotation_direction = random.choice([-1 if randomize_rotation_direction else 1, 1])
        max_rotation_duration_towards_target = 0.1
        min_moving_towards_target_duration = 0.2
        max_moving_towards_target_duration = 1.5

        last_action_timestamp = 0
        last_rotation_timestamp = datetime.now().timestamp()
        is_looking_for_target = False
        is_rotating_toward_target = False
        is_following_target = False

        while self.__targeting_process is not None:  # and self.__detector.id() == detector_id:
            now = datetime.now().timestamp()

            # Wait some time after previous action
            if now - last_action_timestamp < next_action_delay:
                continue

            last_target_detection_timestamp = 0 if self.__last_target_detection is None else \
                self.__last_target_detection['timestamp']

            # If there is no target detected for given amount of time
            if self.__last_target_detection is None or now - last_target_detection_timestamp > idle_time:
                if now - last_rotation_timestamp > rotation_interval:
                    last_rotation_timestamp = now
                    rotation_duration = random.uniform(1, 3)  # must not be larger than rotation_interval
                    rotation_direction = random.choice([-1 if randomize_rotation_direction else 1, 1])
                    is_looking_for_target = False
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
                estimated_distance = min(1, max(0, 1 - self.__last_target_detection['area']))

                rotation_duration_towards_target = abs(target_position_x) * max_rotation_duration_towards_target
                moving_towards_target_duration = max(min_moving_towards_target_duration,
                                                     estimated_distance * max_moving_towards_target_duration)

                # Rotate slightly towards target
                if now - last_target_detection_timestamp < rotation_duration_towards_target and not is_following_target:
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
                    last_action_timestamp = now

    def __handle_target_detection(self, detections: list[Detection]):  # position: Tuple[float, float], area: float):
        self.__view.set_detections(detections)

        if len(detections) <= 0:
            return

        best_detection = detections[0]

        gui_width, gui_height = self._gui.get_size()
        center = (
            ((best_detection.bounding_box.left + best_detection.bounding_box.right) / 2) / gui_width * 2.0 - 1.0,
            ((best_detection.bounding_box.top + best_detection.bounding_box.bottom) / 2) / gui_height * 2.0 - 1.0
        )
        normalized_area = abs(
            best_detection.bounding_box.right - best_detection.bounding_box.left) / gui_width * abs(
            best_detection.bounding_box.bottom - best_detection.bounding_box.top) / gui_height

        print("Target detected at position:", center, "with area:", normalized_area)

        self.__last_target_detection = {
            'position': center,
            'area': normalized_area,
            'timestamp': datetime.now().timestamp()
        }

    def __targeting_thread(self, *object_names: str):
        self.__is_targeting = True

        loud_print(f"Starting targeting objects: {object_names}", True)

        self._gui.start_camera_preview()
        self.__view.toggle_fill_buttons(False)
        self.__view.toggle_depth_preview(True)

        while self.__is_targeting:
            start = time.time()

            image = self._gui.get_last_camera_frame()
            if image is None:
                continue

            detections = self.__detector.detect(image)
            self.__handle_target_detection(list(filter(lambda d: d.categories[0].label in object_names, detections)))

            depth_estimation = self.__depth.estimate(image)
            self.__view.set_depth_estimation_image(depth_estimation)

            fps = min(30.0, 1 / (time.time() - start))
            print("FPS:", fps)

    def __start_targeting_objects(self, *object_names: str):
        if self.__targeting_process is not None:
            print("There is already a targeting objects process running")
            return

        self.__targeting_process = Thread(target=self.__targeting_thread, daemon=True, args=object_names)
        self.__targeting_process.start()

        if self.__movement_thread is None:
            self.__movement_thread = Thread(target=self.__smart_movement_thread, daemon=True)
            self.__movement_thread.start()
