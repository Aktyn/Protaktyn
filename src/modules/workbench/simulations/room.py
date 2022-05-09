import random
from math import cos, sin, pi, sqrt
from typing import Optional

import pymunk
from pynput import keyboard
from src.common.math import mix
from src.gui.core.gui import GUI
from src.modules.workbench.simulations.simulation_base import SimulationBase


# NOTE: All length/size values in this file should be in meters except of RoomSimulation.SCALE which allows for a reasonable size preview

class _Steering:
    def __init__(self):
        self.FORWARD = False
        self.BACKWARD = False
        self.LEFT = False
        self.RIGHT = False


class RoomSimulation(SimulationBase):
    SENSOR_RANGE = 2
    SCALE = 0.1

    class _Robot:
        def __init__(self, steering: Optional[_Steering] = None, pos=(0., 0.)):
            self.__steering = steering
            self.__movement_speed = 0.1
            self.__rotation_speed = pi * 0.75
            self.__box = SimulationBase._Box(pos=pos, size=(0.15 * RoomSimulation.SCALE, 0.3 * RoomSimulation.SCALE),
                                             color=(255, 196, 128))
            # Prevent from colliding with other robots
            self.__box.body.set_collision_filtering(categories=0x0002, mask=0xFFFFFFFF ^ 0x0002)
            for shape in self.__box.body.shapes:
                shape.friction = 0.99
                shape.elasticity = 0.01

            self.__sensor_color = (128, 255, 128)
            self.__active_sensor_color = (128, 128, 255)

            self.__proximity_sensors = (
                SimulationBase._Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color),
                SimulationBase._Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color),
                SimulationBase._Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color)
                # SimulationBase._Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color)
            )

        def objects(self):
            return *self.__proximity_sensors, self.__box

        def pos(self):
            return self.__box.pos

        def update(self, _delta_time: float, simulation: SimulationBase):
            if self.__steering is not None:
                if self.__steering.FORWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * self.__movement_speed,
                         sin(self.__box.body.angle + pi / 2.0) * self.__movement_speed)
                    )
                if self.__steering.BACKWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * -self.__movement_speed,
                         sin(self.__box.body.angle + pi / 2.0) * -self.__movement_speed)
                    )
                if self.__steering.LEFT:
                    self.__box.body.set_angular_velocity(self.__rotation_speed)
                if self.__steering.RIGHT:
                    self.__box.body.set_angular_velocity(-self.__rotation_speed)

            for i, sensor in enumerate(self.__proximity_sensors):
                c = cos(self.__box.body.angle + pi / 2.0 * float(i))
                s = sin(self.__box.body.angle + pi / 2.0 * float(i))

                offset_len = (self.__box.size[0 if i % 2 == 0 else 1] / 2.0)

                sensor.pos = (
                    c * offset_len + self.__box.pos[0],
                    s * offset_len + self.__box.pos[1]
                )
                sensor.pos_end = (
                    c * (offset_len + RoomSimulation.SENSOR_RANGE * RoomSimulation.SCALE) + self.__box.pos[0],
                    s * (offset_len + RoomSimulation.SENSOR_RANGE * RoomSimulation.SCALE) + self.__box.pos[1]
                )

                contact_point = simulation._ray_cast(sensor.pos, sensor.pos_end, 0xFFFFFFFF ^ 0x0002)
                if contact_point is not None:
                    normalized_distance = sqrt((contact_point[0] - sensor.pos[0]) ** 2 + (
                            contact_point[1] - sensor.pos[1]) ** 2) / (
                                                  RoomSimulation.SENSOR_RANGE * RoomSimulation.SCALE)
                    # print(distance)
                    # self._add_objects(SimulationBase._Box(pos=contact_point, size=(0.003, 0.003), color=(0, 0, 0),
                    #                                       sensor=True))

                    sensor.set_color((
                        mix(self.__sensor_color[0], self.__active_sensor_color[0],
                            sqrt(max(0., 1.0 - normalized_distance))),
                        mix(self.__sensor_color[1], self.__active_sensor_color[1],
                            sqrt(max(0., 1.0 - normalized_distance))),
                        mix(self.__sensor_color[2], self.__active_sensor_color[2],
                            sqrt(max(0., 1.0 - normalized_distance))),
                    ))
                else:
                    sensor.set_color(self.__sensor_color)

    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)

        self.__destination = SimulationBase._Box(pos=(1.25 * self.SCALE, 7.5 * self.SCALE),
                                                 size=(0.5 * self.SCALE, 0.5 * self.SCALE), color=(225, 208, 77),
                                                 dynamic=False, sensor=True)

        self.__listener = keyboard.Listener(on_press=lambda key: self.__on_press(key, True),
                                            on_release=lambda key: self.__on_press(key, False))
        self.__listener.start()

        self.__keyboard_steering = _Steering()

        self.__robots = (
            self._Robot(steering=self.__keyboard_steering, pos=(0, 0)),
            *tuple(map(lambda _: self._Robot(pos=(
                random.uniform(-0.4 * self.SCALE, 0.4 * self.SCALE),
                random.uniform(-0.44 * self.SCALE, 0.4 * self.SCALE)
            )), range(5)))
        )

        super()._start()

    def close(self):
        self.__listener.stop()
        super().close()

    def _init(self):
        # self._add_objects(
        #     *map(lambda i: SimulationBase._Box(pos=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4))), range(10))
        # )

        wall_color = (218, 168, 159)

        self._add_objects(
            SimulationBase._Box(pos=(0 * self.SCALE, -1.5 * self.SCALE),
                                size=(3.5 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=((-0.5 - 0.75) * self.SCALE, 1 * self.SCALE),
                                size=(1 * self.SCALE, 4 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=((0.5 + 0.75) * self.SCALE, 1 * self.SCALE),
                                size=(1 * self.SCALE, 4 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(0.55 * self.SCALE, 1.3 * self.SCALE),
                                size=(0.4 * self.SCALE, 1.5 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(0 * self.SCALE, 4.5 * self.SCALE),
                                size=(3.5 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(2.25 * self.SCALE, 3.5 * self.SCALE),
                                size=(1 * self.SCALE, 3 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-2.75 * self.SCALE, 2.5 * self.SCALE),
                                size=(2 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-4.25 * self.SCALE, 5.5 * self.SCALE),
                                size=(1 * self.SCALE, 7 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-0.5 * self.SCALE, 8.5 * self.SCALE),
                                size=(6.5 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-1.25 * self.SCALE, 6 * self.SCALE),
                                size=(1 * self.SCALE, 2 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(1 * self.SCALE, 6.5 * self.SCALE),
                                size=(3.5 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(2.25 * self.SCALE, 7.5 * self.SCALE),
                                size=(1 * self.SCALE, 1 * self.SCALE), color=wall_color, dynamic=False),
            self.__destination,
        )

        for robot in self.__robots:
            self._add_objects(*robot.objects())

    def __on_press(self, key, toggle: bool):
        # noinspection PyBroadException
        try:
            k = key.char
        except BaseException:
            k = key.name

        if k == 'w' or k == 'up':
            self.__keyboard_steering.FORWARD = toggle
        elif k == 's' or k == 'down':
            self.__keyboard_steering.BACKWARD = toggle
        elif k == 'a' or k == 'left':
            self.__keyboard_steering.LEFT = toggle
        elif k == 'd' or k == 'right':
            self.__keyboard_steering.RIGHT = toggle

    def _update(self, delta_time: float):
        # self.__robot.update(delta_time, self)
        for robot in self.__robots:
            robot.update(delta_time, self)
        self._set_camera_pos(self.__robots[0].pos())
