import random
import time
from math import cos, sin, pi, sqrt
from src.common.math import mix
from src.gui.core.gui import GUI
from src.gui.core.widget import Widget
from src.modules.workbench.common.steering import Steering, KeyboardSteering
from src.modules.workbench.evolution.evolution import Evolution
from src.modules.workbench.neural_network.network import NeuralNetwork
from src.modules.workbench.neural_network.visualize import visualize_network
from src.modules.workbench.simulations.simulation_base import SimulationBase


# NOTE: All length/size values in this file should be in meters except of RoomSimulation.SCALE which allows for a reasonable size preview


class RoomSimulation(SimulationBase):
    _SENSOR_RANGE = 2
    _SCALE = 0.1
    __POPULATION = 50  # 200
    __LAYERS = [3, 8, 2]
    __STEERING_THRESHOLD = 1 / 3
    __ROUND_DURATION = 10  # 30 seconds

    class _Robot:
        def __init__(self, steering: Steering = Steering(), pos=(0., 0.)):
            self.steering = steering
            self.__movement_speed = 0.1
            self.__rotation_speed = pi * 0.75
            self.__box = SimulationBase._Box(pos=pos, size=(0.15 * RoomSimulation._SCALE, 0.3 * RoomSimulation._SCALE),
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
            self.__proximity_sensors_values = list(map(lambda _: 0., self.__proximity_sensors))

        def objects(self):
            return *self.__proximity_sensors, self.__box

        @property
        def pos(self):
            return self.__box.pos

        def get_sensors_values(self):
            return self.__proximity_sensors_values

        def update(self, _delta_time: float, simulation: SimulationBase):
            if self.steering is not None:
                if self.steering.FORWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * self.__movement_speed,
                         sin(self.__box.body.angle + pi / 2.0) * self.__movement_speed)
                    )
                if self.steering.BACKWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * -self.__movement_speed,
                         sin(self.__box.body.angle + pi / 2.0) * -self.__movement_speed)
                    )
                if self.steering.LEFT:
                    self.__box.body.set_angular_velocity(self.__rotation_speed)
                if self.steering.RIGHT:
                    self.__box.body.set_angular_velocity(-self.__rotation_speed)

            for i, sensor in enumerate(self.__proximity_sensors):
                c = cos(self.__box.body.angle + pi / 2.0 * float(i))
                s = sin(self.__box.body.angle + pi / 2.0 * float(i))

                # offset_len = (self.__box.size[0 if i % 2 == 0 else 1] / 2.0) - 0.075 * RoomSimulation._SCALE
                offset_len = 0.

                sensor.pos = (
                    c * offset_len + self.__box.pos[0],
                    s * offset_len + self.__box.pos[1]
                )
                sensor.pos_end = (
                    c * (offset_len + RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE) + self.__box.pos[0],
                    s * (offset_len + RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE) + self.__box.pos[1]
                )

                contact_point = simulation._ray_cast(sensor.pos, sensor.pos_end, 0xFFFFFFFF ^ 0x0002)
                if contact_point is not None:
                    normalized_distance = sqrt((contact_point[0] - sensor.pos[0]) ** 2 + (
                            contact_point[1] - sensor.pos[1]) ** 2) / (
                                                  RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE)
                    self.__proximity_sensors_values[i] = 1.0 - normalized_distance
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
                    self.__proximity_sensors_values[i] = 0.0
                    sensor.set_color(self.__sensor_color)

    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)
        self.__round_start_timestamp = 0.

        self.__destination = SimulationBase._Box(pos=(1.25 * self._SCALE, 7.5 * self._SCALE),
                                                 size=(0.5 * self._SCALE, 0.5 * self._SCALE), color=(225, 208, 77),
                                                 dynamic=False, sensor=True)

        self.__population = list(map(lambda _: (
            self._Robot(pos=(
                random.uniform(-0.4 * self._SCALE, 0.4 * self._SCALE),
                random.uniform(-0.44 * self._SCALE, 0.4 * self._SCALE)
            )),
            NeuralNetwork(self.__LAYERS)
        ), range(self.__POPULATION)))
        self.__evolution = Evolution(list(map(lambda individual: individual[1], self.__population)))

        self.__network_visualization_widgets: list[Widget] = []
        self.__last_visualization_timestamp = 0.

        self.__keyboard_steering = KeyboardSteering()
        self.__player = self._Robot(steering=self.__keyboard_steering, pos=(0, 0))

        super()._start()

    def close(self):
        self.__keyboard_steering.close()
        self._gui.remove_widgets(*self.__network_visualization_widgets)
        super().close()

    def _on_init(self):
        wall_color = (218, 168, 159)

        self._add_objects(
            SimulationBase._Box(pos=(0 * self._SCALE, -1.5 * self._SCALE),
                                size=(3.5 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=((-0.5 - 0.75) * self._SCALE, 1 * self._SCALE),
                                size=(1 * self._SCALE, 4 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=((0.5 + 0.75) * self._SCALE, 1 * self._SCALE),
                                size=(1 * self._SCALE, 4 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(0.55 * self._SCALE, 1.3 * self._SCALE),
                                size=(0.4 * self._SCALE, 1.5 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(0 * self._SCALE, 4.5 * self._SCALE),
                                size=(3.5 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(2.25 * self._SCALE, 3.5 * self._SCALE),
                                size=(1 * self._SCALE, 3 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-2.75 * self._SCALE, 2.5 * self._SCALE),
                                size=(2 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-4.25 * self._SCALE, 5.5 * self._SCALE),
                                size=(1 * self._SCALE, 7 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-0.5 * self._SCALE, 8.5 * self._SCALE),
                                size=(6.5 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(-1.25 * self._SCALE, 6 * self._SCALE),
                                size=(1 * self._SCALE, 2 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(1 * self._SCALE, 6.5 * self._SCALE),
                                size=(3.5 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            SimulationBase._Box(pos=(2.25 * self._SCALE, 7.5 * self._SCALE),
                                size=(1 * self._SCALE, 1 * self._SCALE), color=wall_color, dynamic=False),
            self.__destination,
        )

        for robot, _ in self.__population:
            self._add_objects(*robot.objects())
        self._add_objects(*self.__player.objects())

        self.__round_start_timestamp = time.time()

    def __start_next_round(self):
        # TODO: determine whether destination is visible by robot (wall doesn't obstacle it);
        # TODO: also measure distance moved by robot to favor robots that are getting to the destination by shortest path
        # TODO: finish round earlier if all robots are stuck around same position for certain amount of time
        destination_pos = self.__destination.pos

        # Calculate score for each individual
        scores: list[float] = list(
            map(lambda individual: (10 * self._SCALE) - sqrt((individual[0].pos[0] - destination_pos[0]) ** 2 +
                                                             (individual[0].pos[1] - destination_pos[1]) ** 2),
                self.__population))

        self.__evolution.evolve(scores)
        self.__evolution.print_stats()

    def _on_update(self, delta_time: float):
        now = time.time()

        if now - self.__round_start_timestamp > self.__ROUND_DURATION:
            self.__round_start_timestamp = now
            self.__start_next_round()

        for robot, network in self.__population:
            prediction = network.calculate(robot.get_sensors_values())
            if len(prediction) != self.__LAYERS[-1]:
                raise ValueError("Network output size does not match number of neurons in last layer of network")

            robot.steering.FORWARD = prediction[0] > self.__STEERING_THRESHOLD
            robot.steering.BACKWARD = prediction[0] < -self.__STEERING_THRESHOLD
            robot.steering.LEFT = prediction[1] > self.__STEERING_THRESHOLD
            robot.steering.RIGHT = prediction[1] < -self.__STEERING_THRESHOLD

            robot.update(delta_time, self)

        self.__player.update(delta_time, self)
        self._set_camera_pos(self.__player.pos)

        # Keep an eye on the first robot
        # self._set_camera_pos(self.__population[0][0].pos)

        if now - self.__last_visualization_timestamp > 1 / 30:
            self.__last_visualization_timestamp = now
            self._gui.remove_widgets(*self.__network_visualization_widgets)
            self.__network_visualization_widgets = visualize_network(self.__population[0][1])
            if self._is_running:
                self._gui.add_widgets(tuple(self.__network_visualization_widgets))
