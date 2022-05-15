import random
import time
from math import cos, sin, pi, sqrt, inf

from pymunk import Arbiter, Space

from src.common.math import mix
from src.gui.core.gui import GUI
from src.gui.core.widget import Widget
from src.modules.workbench.common.steering import Steering, KeyboardSteering
from src.modules.workbench.evolution.evolution import Evolution, EvolutionConfig
from src.modules.workbench.neural_network.network import NeuralNetwork
from src.modules.workbench.neural_network.visualize import visualize_network
from src.modules.workbench.simulations.simulation_base import SimulationBase


# NOTE: All length/size values in this file should be in meters except of RoomSimulation.SCALE which allows for a reasonable size preview


class RoomSimulation(SimulationBase):
    _SENSOR_RANGE = 2
    _SCALE = 0.1
    __POPULATION_SIZE = 150
    __RENDER_POPULATION_SIZE = 50
    __LAYERS = [3, 8, 2]
    __STEERING_THRESHOLD = 1 / 3
    __ROUND_DURATION = 25
    _STUCK_DURATION = 5
    _STUCK_DISTANCE_THRESHOLD = 1
    _SAFE_DISTANCE_FROM_WALL = 0.10
    _RENDER_SENSORS = False
    __POINTS_DISTANCE = 0.5

    class _Robot:
        def __init__(self, steering: Steering = Steering(), pos=(0., 0.), can_stuck=True, render=True):
            self.__delta_timer = 0.0
            self.__arrived = False
            self.__arrived_time = 0.0
            self.__stuck = False
            self.__stuck_time = 0.0
            self.__can_stuck = can_stuck
            self.__last_position_check_timestamp = 0
            self.__last_position_check_position = (0., 0.)

            self.__moved_distance = 0.0
            self.__last_position = (0., 0.)

            self.steering = steering
            self.__movement_speed = 0.1
            self.__rotation_speed = pi * 0.75
            self.__box = SimulationBase._Box(pos=pos, size=(0.15 * RoomSimulation._SCALE, 0.3 * RoomSimulation._SCALE),
                                             color=(255, 196, 128), collision_type=0x0002, render=render)
            # Prevent from colliding with other robots
            self.__box.body.set_collision_filtering(categories=0x0002, mask=0xFFFFFFFF ^ 0x0002)
            for shape in self.__box.body.shapes:
                shape.friction = 0.99
                shape.elasticity = 0.01

            self.__sensor_color = (128, 255, 128)
            self.__active_sensor_color = (128, 128, 255)

            sensors_count = 3

            self.__proximity_sensors: list[SimulationBase._Line] = list(
                map(lambda _: SimulationBase._Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color,
                                                   render=render and RoomSimulation._RENDER_SENSORS),
                    range(sensors_count))
            )
            self.__proximity_sensors_values = list(map(lambda _: 0., range(sensors_count)))

        def __delta_now(self):
            return self.__delta_timer

        def objects(self):
            return *self.__proximity_sensors, self.__box

        def set_arrived(self):
            self.__arrived = True
            self.__arrived_time = self.__delta_timer
            self.__box.set_color((128, 255, 128))

        @property
        def arrived(self):
            return self.__arrived

        @property
        def arrived_time(self):
            return self.__arrived_time

        @property
        def pos(self):
            return self.__box.pos

        @property
        def shape(self):
            return self.__box.shape

        @property
        def stuck(self):
            return self.__stuck

        @property
        def stuck_time(self):
            return self.__stuck_time

        @property
        def moved_distance(self):
            return self.__moved_distance

        def register_path_distance(self, distance: float):
            # self.__moved_distance = max(distance, self.__moved_distance)
            self.__moved_distance = distance

        def respawn(self):
            self.__arrived = False
            self.__arrived_time = 0.0
            self.__stuck = False
            self.__stuck_time = 0.0
            self.__delta_timer = 0.0
            self.__last_position_check_timestamp = 0
            self.__last_position_check_position = (0., 0.)
            self.__box.set_color((255, 196, 128))
            self.__proximity_sensors_values = [0.] * len(self.__proximity_sensors_values)

            self.__moved_distance = 0.0
            self.__last_position = (0., 0.)

            self.__box.body.set_position((0., 0.))
            self.__box.body.set_angle(0)
            self.__box.body.set_velocity((0., 0.))
            self.__box.body.set_angular_velocity(0)

        def get_sensors_values(self):
            return self.__proximity_sensors_values

        def update(self, delta_time: float, simulation: SimulationBase):
            self.__delta_timer += delta_time

            if self.__stuck or self.__arrived:
                return
            elif self.__can_stuck:
                dst_squared = (self.pos[0] - self.__last_position_check_position[0]) ** 2 + \
                              (self.pos[1] - self.__last_position_check_position[1]) ** 2
                if dst_squared > (RoomSimulation._STUCK_DISTANCE_THRESHOLD * RoomSimulation._SCALE) ** 2:
                    self.__last_position_check_position = (self.pos[0], self.pos[1])
                    self.__last_position_check_timestamp = self.__delta_timer
                elif self.__delta_timer - self.__last_position_check_timestamp > RoomSimulation._STUCK_DURATION:
                    self.__last_position_check_timestamp = self.__delta_timer
                    self.__stuck = True
                    self.__stuck_time = self.__delta_timer
                    self.__box.set_color((197, 190, 176))

            self.__last_position = (self.pos[0], self.pos[1])

            touching_wall = False
            for i, sensor in enumerate(self.__proximity_sensors):
                c = cos(self.__box.body.angle + pi / 2.0 * float(i))
                s = sin(self.__box.body.angle + pi / 2.0 * float(i))

                # offset_len = (self.__box.size[0 if i % 2 == 0 else 1] / 2.0)
                offset_len = 0 if i % 2 == 0 else (self.__box.size[0] / 2.0)
                # offset_len = 0.

                sensor.set_positions((
                    c * offset_len + self.__box.pos[0],
                    s * offset_len + self.__box.pos[1]
                ), (
                    c * (offset_len + RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE) + self.__box.pos[0],
                    s * (offset_len + RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE) + self.__box.pos[1]
                ))

                contact_point = simulation._ray_cast(from_point=sensor.pos, to_point=sensor.pos_end,
                                                     mask=0xFFFFFFFF ^ (0x0002 | 0x0004))
                if contact_point is not None:
                    distance = sqrt((contact_point[0] - sensor.pos[0]) ** 2 + (contact_point[1] - sensor.pos[1]) ** 2)

                    # if self.__can_stuck and distance < RoomSimulation._SAFE_DISTANCE_FROM_WALL * RoomSimulation._SCALE + \
                    #         (self.__box.size[0] / 2.0):
                    #     self.__stuck = True
                    #     self.__stuck_time = self.__delta_timer
                    #     self.__box.set_color((197, 190, 176))
                    if not touching_wall and distance < RoomSimulation._SAFE_DISTANCE_FROM_WALL * RoomSimulation._SCALE + (
                            self.__box.size[0] / 2.0):
                        touching_wall = True

                    normalized_distance = distance / (RoomSimulation._SENSOR_RANGE * RoomSimulation._SCALE)
                    self.__proximity_sensors_values[i] = 1.0 - normalized_distance

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

            if self.steering is not None:
                speed = self.__movement_speed if not touching_wall else self.__movement_speed * 0.2
                rotation_speed = self.__rotation_speed if not touching_wall else self.__rotation_speed * 0.2

                if self.steering.FORWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * speed,
                         sin(self.__box.body.angle + pi / 2.0) * speed)
                    )
                if self.steering.BACKWARD:
                    self.__box.body.set_velocity(
                        (cos(self.__box.body.angle + pi / 2.0) * -speed,
                         sin(self.__box.body.angle + pi / 2.0) * -speed)
                    )
                if self.steering.LEFT:
                    self.__box.body.set_angular_velocity(rotation_speed)
                if self.steering.RIGHT:
                    self.__box.body.set_angular_velocity(-rotation_speed)

    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)
        self.__round_duration_timer = 0.

        self.__destination = SimulationBase._Box(pos=(1.25 * self._SCALE, 7.5 * self._SCALE),
                                                 size=(1 * self._SCALE, 1 * self._SCALE), color=(225, 208, 77),
                                                 dynamic=False, sensor=False, collision_type=0x0004)
        self.__destination.body.set_collision_filtering(categories=0x0004, mask=0xFFFFFFFF)

        path = [
            (0., 0.),
            (0., 3.5),
            (-2.75, 3.5),
            (-2.75, 7.5),
            (1.25, 7.5),
        ]

        self.__path_points: list[tuple[float, float]] = []

        for p_i in range(len(path) - 1):
            x1, y1 = path[p_i]
            x2, y2 = path[p_i + 1]
            segment_length = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) * self._SCALE
            d = 0.0
            if segment_length < 1e-6:
                continue
            while d < segment_length:
                xx = x1 + (x2 - x1) * d / segment_length
                yy = y1 + (y2 - y1) * d / segment_length
                self.__path_points.append((xx * self._SCALE, yy * self._SCALE))
                d += self.__POINTS_DISTANCE * self._SCALE

        self.__robots = list(map(lambda index: self._Robot(pos=(
            random.uniform(-0.4 * self._SCALE, 0.4 * self._SCALE),
            random.uniform(-0.44 * self._SCALE, 0.4 * self._SCALE)
        ), render=index < self.__RENDER_POPULATION_SIZE), range(self.__POPULATION_SIZE)))

        self.__evolution = Evolution[NeuralNetwork](
            genomes=list(
                map(lambda _: NeuralNetwork(self.__LAYERS, randomize_weights=True), range(self.__POPULATION_SIZE))),
            evolution_config=EvolutionConfig(
                elitism=4 / float(self.__POPULATION_SIZE),
                mutation_chance=0.1,
                mutation_scale=1
            )
        )

        self.__network_visualization_widgets: list[Widget] = []
        self.__last_visualization_timestamp = 0.

        self.__keyboard_steering = KeyboardSteering()
        self.__player = self._Robot(steering=self.__keyboard_steering, pos=(0, 0), can_stuck=False)

        super().add_collision_handler(0x0002, 0x0004, self.__on_robot_to_destination_collision)

        super()._start()

    def close(self):
        self.__keyboard_steering.close()
        self._gui.remove_widgets(*self.__network_visualization_widgets)
        super().close()

    def __on_robot_to_destination_collision(self, arbiter: Arbiter, _space: Space, _data: any):
        shape_a, shape_b = arbiter.shapes
        robot_shape = shape_a if shape_b == self.__destination.shape else shape_b
        for robot in [*self.__robots, self.__player]:
            if robot.shape == robot_shape:
                robot.set_arrived()

    def _on_init(self):
        wall_color = (218, 168, 159)

        layout = [
            (0, -1.5, 3.5, 1),
            (-1.25, 1, 1, 4),
            (1.25, 1, 1, 4),
            (0.55, 1.3, 0.4, 1.5),
            (0, 4.5, 3.5, 1),
            (2.25, 3.5, 1, 3),
            (-2.75, 2.5, 2, 1),
            (-4.25, 5.5, 1, 7),
            (-0.5, 8.5, 6.5, 1),
            (-1.25, 6, 1, 2),
            (1, 6.5, 3.5, 1),
            # (2.25, 7.5, 1, 1)
        ]
        for x, y, width, height in layout:
            self._add_objects(SimulationBase._Box(pos=(x * self._SCALE, y * self._SCALE),
                                                  size=(width * self._SCALE, height * self._SCALE), color=wall_color,
                                                  dynamic=False))

        for xx, yy in self.__path_points:
            self._add_objects(SimulationBase._Box(pos=(xx, yy),
                                                  size=(0.05 * self._SCALE, 0.05 * self._SCALE),
                                                  color=(216, 147, 206), dynamic=False, sensor=True))

        self._add_objects(self.__destination)

        for robot in self.__robots:
            self._add_objects(*robot.objects())
        self._add_objects(*self.__player.objects())

        self.__round_duration_timer = 0.

    def __start_next_round(self):
        def rate_robot(robot_: RoomSimulation._Robot):
            # obstacles_to_destination = self._ray_cast_all(robot_.pos, self.__destination.pos, 0xFFFFFFFF ^ 0x0002)
            # obstacles_count = max(0, (len(obstacles_to_destination) - 1))

            # obstacles_score = 1 if obstacles_count == 0 else -0.1 * obstacles_count

            # destination_distance_squared = (robot_.pos[0] - self.__destination.pos[0]) ** 2 + \
            #                               (robot_.pos[1] - self.__destination.pos[1]) ** 2

            # Note that 1 is maximum distance_score value
            # destination_distance_score = (1.0 - sqrt(destination_distance_squared)) * 0.5

            # Note that robot is rewarded for more moved distance if it has not reached the destination.
            # This is to favor robots that are not stucking in place
            moved_distance_score = 2 + (
                        1.0 - robot_.arrived_time / RoomSimulation.__ROUND_DURATION) * 2 if robot_.arrived \
                else robot_.moved_distance

            stuck_time_score = -(RoomSimulation.__ROUND_DURATION - robot_.stuck_time) / RoomSimulation.__ROUND_DURATION \
                if robot_.stuck else 0

            # sensor_values = robot_.get_sensors_values()
            # wall_distance_score = -max(sensor_values) * 0.1

            # print(moved_distance_score, wall_distance_score, stuck_time_score)
            return moved_distance_score + stuck_time_score

        # Calculate score for each individual
        scores: list[float] = list(map(rate_robot, self.__robots))

        self.__evolution.evolve(scores)
        self.__evolution.print_stats()

        for robot in self.__robots:
            robot.respawn()

    def __calculate_robot_path_distance(self, robot: _Robot):
        closest_point_index = 0
        closest_point_distance = inf
        for i, point in enumerate(self.__path_points):
            point_distance = sqrt((point[0] - robot.pos[0]) ** 2 + (point[1] - robot.pos[1]) ** 2)
            if point_distance < closest_point_distance:
                closest_point_distance = point_distance
                closest_point_index = i

        points_difference_factor = 0.
        if closest_point_index < len(self.__path_points) - 1:
            next_x, next_y = self.__path_points[closest_point_index + 1]
            next_point_distance = sqrt((next_x - robot.pos[0]) ** 2 + (next_y - robot.pos[1]) ** 2)
            points_difference_factor = 1.0 - abs(closest_point_distance - next_point_distance) / (
                    self.__POINTS_DISTANCE * self._SCALE)
        return (closest_point_index + points_difference_factor) / len(self.__path_points)

    def _on_update(self, delta_time: float):
        all_robots_are_stuck = True

        for i in range(self.__POPULATION_SIZE):
            robot = self.__robots[i]
            if not robot.stuck:
                all_robots_are_stuck = False
            network = self.__evolution.individuals[i].genome  # type: NeuralNetwork

            prediction = network.calculate(robot.get_sensors_values())
            if len(prediction) != self.__LAYERS[-1]:
                raise ValueError("Network output size does not match number of neurons in last layer of network")

            robot.steering.FORWARD = prediction[0] > self.__STEERING_THRESHOLD
            robot.steering.BACKWARD = prediction[0] < -self.__STEERING_THRESHOLD
            robot.steering.LEFT = prediction[1] > self.__STEERING_THRESHOLD
            robot.steering.RIGHT = prediction[1] < -self.__STEERING_THRESHOLD

            robot.update(delta_time, self)

            robot.register_path_distance(self.__calculate_robot_path_distance(robot))

        self.__player.update(delta_time, self)
        self._set_camera_pos(self.__player.pos)

        self.__round_duration_timer += delta_time
        if all_robots_are_stuck or self.__round_duration_timer >= self.__ROUND_DURATION:
            # remaining_round_duration = max(0.0, self.__ROUND_DURATION - self.__round_duration_timer)
            self.__round_duration_timer = 0
            self.__start_next_round()

        # Keep an eye on the first and also the best robot
        # self._set_camera_pos(self.__population[0].pos)

        # Update neural network visualization with some frequency
        now = time.time()
        if now - self.__last_visualization_timestamp > 0.1:
            self.__last_visualization_timestamp = now
            self._gui.remove_widgets(*self.__network_visualization_widgets)
            self.__network_visualization_widgets = visualize_network(self.__evolution.individuals[0].genome)
            if self._is_running:
                self._gui.add_widgets(tuple(self.__network_visualization_widgets))
