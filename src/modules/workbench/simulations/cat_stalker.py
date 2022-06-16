import random
import math
from typing import Optional

from src.common.math_utils import distance_sqr
from src.gui.core.gui import GUI
from src.modules.robot.robot_controller import RobotController
from src.modules.workbench.common.steering import Steering, KeyboardSteering
from src.modules.workbench.simulations.physics_simulation_base import PhysicsSimulationBase
from src.modules.workbench.simulations.robot import Robot
from src.modules.workbench.simulations.room import RoomSimulation


class CatStalkerSimulation(PhysicsSimulationBase):
    _SCALE = 0.1
    __CAT_DETECTION_FREQUENCY = 1  # Simulates frequency of tensorflow objects detection from camera image

    class _Cat:
        __STEERING_CHANGE_FREQUENCY = 1

        def __init__(self, scale: float, pos=(0, 0)):
            self.__scale = scale
            self.__movement_speed = 0.1
            self.__rotation_speed = math.pi * 0.5

            self.__box = PhysicsSimulationBase.Box(pos=pos,
                                                   size=(0.4 * self.__scale, 0.4 * self.__scale),
                                                   color=(128, 255, 128), collision_type=0x0008)
            for shape in self.__box.body.shapes:
                shape.friction = 0.99
                shape.elasticity = 0.01

            self.__steering = Steering()
            self.__steering_change_timer = 0

        def objects(self):
            return self.__box

        @property
        def pos(self):
            return self.__box.pos

        def update(self, delta_time: float):
            self.__steering_change_timer += delta_time

            if self.__steering_change_timer > self.__STEERING_CHANGE_FREQUENCY:
                self.__steering_change_timer -= self.__STEERING_CHANGE_FREQUENCY

                do_nothing = random.random() < 0.75
                self.__steering.LEFT = random.random() > 0.5 if not do_nothing else False
                self.__steering.RIGHT = random.random() > 0.5 if not do_nothing else False
                self.__steering.FORWARD = random.random() > 0.5 if not do_nothing else False
                self.__steering.BACKWARD = random.random() > 0.5 if not do_nothing else False

            if self.__steering.FORWARD:
                self.__box.body.set_velocity(
                    (math.cos(self.__box.body.angle + math.pi / 2.0) * self.__movement_speed,
                     math.sin(self.__box.body.angle + math.pi / 2.0) * self.__movement_speed)
                )
            if self.__steering.BACKWARD:
                self.__box.body.set_velocity(
                    (math.cos(self.__box.body.angle + math.pi / 2.0) * -self.__movement_speed,
                     math.sin(self.__box.body.angle + math.pi / 2.0) * -self.__movement_speed)
                )
            if self.__steering.LEFT:
                self.__box.body.set_angular_velocity(self.__rotation_speed)
            if self.__steering.RIGHT:
                self.__box.body.set_angular_velocity(-self.__rotation_speed)

    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)

        self.__cat = CatStalkerSimulation._Cat(
            scale=CatStalkerSimulation._SCALE,
            pos=(1.25 * CatStalkerSimulation._SCALE, 7.5 * CatStalkerSimulation._SCALE)
        )
        self.__robot = Robot(scale=CatStalkerSimulation._SCALE, pos=(0, 0), can_stuck=False,
                             steering=KeyboardSteering())
        self.__robot_controller = RobotController()

        self.__cat_detection_timer = 0.0

        super()._start()

    def close(self):
        super().close()

    def _on_init(self):
        wall_color = (218, 168, 159)

        layout = RoomSimulation.DEFAULT_ROOM_LAYOUT
        for x, y, width, height in layout:
            self._add_objects(PhysicsSimulationBase.Box(pos=(x * self._SCALE, y * self._SCALE),
                                                        size=(width * self._SCALE, height * self._SCALE),
                                                        color=wall_color,
                                                        dynamic=False))

        self._add_objects(*self.__robot.objects())
        self._add_objects(self.__cat.objects())

    def __estimate_cat_position(self) -> Optional[dict[str, float]]:
        max_distance = 3
        max_angle = RobotController.VIEW_ANGLE / 2.0
        cat_robot_distance = distance_sqr(self.__robot.pos, self.__cat.pos) / CatStalkerSimulation._SCALE
        if cat_robot_distance < (max_distance * CatStalkerSimulation._SCALE) ** 2:
            relative_angle = math.atan2(self.__cat.pos[1] - self.__robot.pos[1],
                                        self.__cat.pos[0] - self.__robot.pos[0]) - self.__robot.angle - math.pi / 2.0
            while relative_angle > math.pi:
                relative_angle -= 2 * math.pi
            while relative_angle < -math.pi:
                relative_angle += 2 * math.pi

            if max_angle > relative_angle > -max_angle:
                return {
                    "distance": math.sqrt(cat_robot_distance),
                    "x": relative_angle / max_angle
                }

        return None

    def _on_update(self, delta_time: float):
        self.__cat.update(delta_time)

        estimated_cat_position: Optional[dict[str, float]] = None

        self.__cat_detection_timer += delta_time
        if self.__cat_detection_timer > CatStalkerSimulation.__CAT_DETECTION_FREQUENCY:
            self.__cat_detection_timer -= CatStalkerSimulation.__CAT_DETECTION_FREQUENCY
            estimated_cat_position = self.__estimate_cat_position()
            self.__robot.set_color((255, 1, 0) if estimated_cat_position else Robot.DEFAULT_COLOR)

        movement = self.__robot_controller.update(self.__robot.get_sensors_values(), estimated_cat_position)

        self.__robot.steering.FORWARD = movement[RobotController.Direction.FORWARD]
        self.__robot.steering.BACKWARD = movement[RobotController.Direction.BACKWARD]
        self.__robot.steering.LEFT = movement[RobotController.Direction.LEFT]
        self.__robot.steering.RIGHT = movement[RobotController.Direction.RIGHT]

        self.__robot.update(delta_time, self)
        self._set_camera_pos(self.__robot.pos)
