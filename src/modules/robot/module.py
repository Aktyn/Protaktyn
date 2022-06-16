import time

from threading import Thread
from typing import Optional
from src.common.math_utils import clamp_f
from src.config.commands import Commands
from src.gui.core.gui import GUI
from src.modules.moduleBase import ModuleBase
from src.modules.robot.distance_sensor import DistanceSensor
from src.modules.robot.robot_controller import RobotController
from src.modules.robot.view import RobotView
from src.modules.robot.wheels_controller import WheelsController
from src.object_detection.objectDetector import ObjectDetector, Detection


class RobotModule(ModuleBase):

    def __init__(self, gui: GUI):
        super().__init__(gui)

        self.__view = RobotView(
            on_forward=lambda enable: self.__handle_direction_change(RobotController.Direction.FORWARD, enable),
            on_backward=lambda enable: self.__handle_direction_change(RobotController.Direction.BACKWARD, enable),
            on_turn_left=lambda enable: self.__handle_direction_change(RobotController.Direction.LEFT, enable),
            on_turn_right=lambda enable: self.__handle_direction_change(RobotController.Direction.RIGHT, enable)
        )
        self._gui.set_view(self.__view)

        self.__detector: Optional[ObjectDetector] = None
        self.__movement_thread: Optional[Thread] = None
        self.__last_target_detection: Optional[dict] = None

        self.__wheels = WheelsController()
        self.__current_direction: Optional[RobotController.Direction] = None
        self.__next_direction: Optional[RobotController.Direction] = None

        self.__sensors = [
            DistanceSensor(trig=16, echo=19),  # front (0 deg)
            DistanceSensor(trig=17, echo=27),  # left (45deg)
            DistanceSensor(trig=21, echo=20)  # right (-45deg)
        ]

        super().register_command(Commands.ROBOT.target_cat,  # , 'person'
                                 lambda *args: self.__start_targeting_objects('cat', 'dog', 'horse', 'sheep', 'cow',
                                                                              'bear', 'zebra', 'teddy bear', 'bottle'))

        self.__detector = ObjectDetector(self._gui)
        # self.__depth: Optional[DepthEstimator] = None
        # self.__depth = DepthEstimator(self._gui)

        self.__is_targeting = False
        self.__targeting_process: Optional[Thread] = None

        self.__robot_controller = RobotController()

        # TEMP
        self.__start_targeting_objects('cat', 'dog', 'horse', 'sheep', 'cow', 'bear', 'zebra', 'teddy bear', 'bottle')

    def close(self):
        self.stop_targeting()
        self.__wheels.close()
        self.__detector.close()
        # self.__depth.close()
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

    def __apply_wheels_direction(self, direction: RobotController.Direction):
        if direction == RobotController.Direction.FORWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
            self.__view.set_steering_button_active('forward', True)
        elif direction == RobotController.Direction.BACKWARD:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self.__view.set_steering_button_active('backward', True)
        elif direction == RobotController.Direction.RIGHT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.BACKWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.FORWARD)
            self.__view.set_steering_button_active('right', True)
        elif direction == RobotController.Direction.LEFT:
            self.__wheels.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.FORWARD)
            self.__wheels.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.BACKWARD)
            self.__view.set_steering_button_active('left', True)
        else:
            raise ValueError("Invalid direction")

    def __handle_direction_change(self, direction: RobotController.Direction, enable: bool, force=False):
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

        self.__apply_wheels_direction(direction)

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

        while self.__targeting_process is not None:
            start = time.time()

            distances = [1.0 - clamp_f(sensor.get_distance() / DistanceSensor.RANGE_CM, 0, 1)
                         for sensor in self.__sensors]

            estimated_cat_position = {
                'x': -self.__last_target_detection['position'][0],
                'distance': clamp_f(1.0 - self.__last_target_detection['area'], 0, 1) * 4
            } if self.__last_target_detection is not None else None
            if estimated_cat_position is not None:
                print(f"Cat position: x: {estimated_cat_position['x']}; distance: {estimated_cat_position['distance']}")
            else:
                print(f"Sensors distances: {' | '.join(map(lambda dst: '{0:03d}cm'.format(round(dst)), distances))}")
            movement = self.__robot_controller.update(distances, estimated_cat_position)
            self.__last_target_detection = None

            # self.__handle_direction_change(RobotController.Direction.LEFT, True, True)
            direction = RobotController.Direction.FORWARD if movement[RobotController.Direction.FORWARD] \
                else RobotController.Direction.BACKWARD if movement[RobotController.Direction.BACKWARD] \
                else RobotController.Direction.LEFT if movement[RobotController.Direction.LEFT] \
                else RobotController.Direction.RIGHT if movement[RobotController.Direction.RIGHT] \
                else None

            self.__apply_wheels_direction(direction) if direction is not None else self.__wheels.stop_wheels()

            # Keep the loop at 30 FPS
            elapsed_time = time.time() - start
            time.sleep(max(0.0, 1.0 / 30.0 - elapsed_time))

    def __handle_target_detection(self, detections: list[Detection]):  # position: Tuple[float, float], area: float):
        # print(f"DETECTIONS: {len(detections)}")
        self.__view.set_detections(detections)

        if len(detections) <= 0:
            return

        best_detection = detections[0]

        gui_width, gui_height = self._gui.get_size()
        center = (
            ((best_detection.bounding_box.left + best_detection.bounding_box.right) / 2) / gui_width * 2.0 - 1.0,
            ((best_detection.bounding_box.top + best_detection.bounding_box.bottom) / 2) / gui_height * 2.0 - 1.0
        )
        normalized_area = (
                                  abs(best_detection.bounding_box.right - best_detection.bounding_box.left) *
                                  abs(best_detection.bounding_box.bottom - best_detection.bounding_box.top)
                          ) / (gui_width * gui_height)

        print("Target detected at position:", center, "with area:", normalized_area)

        self.__last_target_detection = {
            'position': center,
            'area': normalized_area,
            # 'timestamp': datetime.now().timestamp()
        }

    def __targeting_thread(self, *object_names: str):
        self.__is_targeting = True

        print(f"Starting targeting objects: {object_names}", True)

        self._gui.start_camera_preview()
        self.__view.toggle_fill_buttons(False)
        self.__view.toggle_depth_preview(True)

        while self.__is_targeting:
            # start = time.time()

            image = self._gui.get_last_camera_frame()
            if image is None:
                continue

            detections = self.__detector.detect(image)
            self.__handle_target_detection(list(filter(lambda d: d.categories[0].label in object_names, detections)))

            # depth_estimation = self.__depth.estimate(image)
            # self.__view.set_depth_estimation_image(depth_estimation)

            # fps = min(30.0, 1 / (time.time() - start))
            # print("FPS:", fps)

    def __start_targeting_objects(self, *object_names: str):
        if self.__targeting_process is not None:
            print("There is already a targeting objects process running")
            return

        self.__targeting_process = Thread(target=self.__targeting_thread, daemon=True, args=object_names)
        self.__targeting_process.start()

        if self.__movement_thread is None:
            self.__movement_thread = Thread(target=self.__smart_movement_thread, daemon=True)
            self.__movement_thread.start()
