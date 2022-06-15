import os
import random
import time
from math import sqrt, inf, ceil
from pymunk import Arbiter, Space
from src.common.common_utils import data_dir
from src.gui.core.gui import GUI
from src.gui.core.rect import Rect
from src.gui.core.widget import Widget
from src.modules.robot.robot_controller import RobotController
from src.modules.workbench.common.steering import KeyboardSteering
from src.modules.workbench.evolution.evolution import Evolution, EvolutionConfig
from src.modules.workbench.neural_network.network import NeuralNetwork
from src.modules.workbench.neural_network.visualize import visualize_network
from src.modules.workbench.simulations.physics_simulation_base import PhysicsSimulationBase
from src.modules.workbench.simulations.robot import Robot
from src.modules.workbench.view import WorkbenchView


# NOTE: All length/size values in this file should be in meters except of RoomSimulation.SCALE which allows for a reasonable size preview
class RoomSimulation(PhysicsSimulationBase):
    __DATA_FILE = os.path.join(data_dir, 'room_evolution.json')
    DEFAULT_ROOM_LAYOUT = [
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
        (2.25, 7.5, 1, 1)
    ]

    _SCALE = 0.1
    __POPULATION_SIZE = 200
    __RENDER_POPULATION_SIZE = 100
    __LAYERS = [3, 8, 2]
    __STEERING_THRESHOLD = 1 / 3
    __ROUND_DURATION = 25
    __POINTS_DISTANCE = 0.5

    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)
        self.__round_duration_timer = 0.

        self.__destination = PhysicsSimulationBase.Box(pos=(1.25 * self._SCALE, 7.5 * self._SCALE),
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

        self.__robots = list(map(lambda index: Robot(scale=RoomSimulation._SCALE, pos=(
            random.uniform(-0.4 * self._SCALE, 0.4 * self._SCALE),
            random.uniform(-0.4 * self._SCALE, 0.4 * self._SCALE)
        ), render=index < self.__RENDER_POPULATION_SIZE), range(self.__POPULATION_SIZE)))

        self.__evolution = Evolution[NeuralNetwork](
            genomes=list(
                map(lambda _: NeuralNetwork(self.__LAYERS, randomize_weights=True), range(self.__POPULATION_SIZE))),
            evolution_config=EvolutionConfig(
                elitism=8 / float(self.__POPULATION_SIZE),
                mutation_chance=0.025,
                mutation_scale=0.3,
                species_maturation_generations=20,
                maximum_species=6,
                species_creation_chance=0.1,
                species_extinction_chance=0.1
            )
        )
        if os.path.isfile(self.__DATA_FILE):
            self.__evolution.load_from_file(self.__DATA_FILE)

        self.__network_visualization_widgets: list[Widget] = []
        self.__last_visualization_timestamp = 0.

        self.__keyboard_steering = KeyboardSteering()
        self.__player = Robot(scale=RoomSimulation._SCALE, steering=self.__keyboard_steering, pos=(0, 0),
                              can_stuck=False)

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

        layout = RoomSimulation.DEFAULT_ROOM_LAYOUT
        for x, y, width, height in layout:
            self._add_objects(PhysicsSimulationBase.Box(pos=(x * self._SCALE, y * self._SCALE),
                                                        size=(width * self._SCALE, height * self._SCALE),
                                                        color=wall_color,
                                                        dynamic=False))

        for xx, yy in self.__path_points:
            self._add_objects(PhysicsSimulationBase.Box(pos=(xx, yy),
                                                        size=(0.05 * self._SCALE, 0.05 * self._SCALE),
                                                        color=(216, 147, 206), dynamic=False, sensor=True))

        # self._add_objects(self.__destination)

        for robot in self.__robots:
            self._add_objects(*robot.objects())
        self._add_objects(*self.__player.objects())

        self.__round_duration_timer = 0.

    def __start_next_round(self):
        def rate_robot(robot_: Robot):
            # obstacles_to_destination = self._ray_cast_all(robot_.pos, self.__destination.pos, 0xFFFFFFFF ^ 0x0002)
            # obstacles_count = max(0, (len(obstacles_to_destination) - 1))

            # obstacles_score = 1 if obstacles_count == 0 else -0.1 * obstacles_count

            # destination_distance_squared = (robot_.pos[0] - self.__destination.pos[0]) ** 2 + \
            #                               (robot_.pos[1] - self.__destination.pos[1]) ** 2

            # Note that 1 is maximum distance_score value
            # destination_distance_score = (1.0 - sqrt(destination_distance_squared)) * 0.5

            # Note that robot is rewarded for more moved distance if it has not reached the destination.
            # This is to favor robots that are not stucking in place
            # moved_distance_score = 2 + (
            #         1.0 - robot_.arrived_time / RoomSimulation.__ROUND_DURATION) * 2 if robot_.arrived \
            #     else robot_.moved_distance

            stuck_time_score = -(RoomSimulation.__ROUND_DURATION - robot_.stuck_time) / RoomSimulation.__ROUND_DURATION \
                if robot_.stuck and not robot_.arrived else 0

            # sensor_values = robot_.get_sensors_values()
            # wall_distance_score = -max(sensor_values) * 0.1

            distance_score = robot_.moved_distance
            velocity_score = (robot_.moved_distance * RoomSimulation.__ROUND_DURATION) / (
                    robot_.distance_record_time + 1.0)
            return distance_score * 5 + velocity_score + stuck_time_score * 40

        # Calculate score for each individual
        scores: list[float] = list(map(rate_robot, self.__robots))

        # Saving best individual to separate file for later use
        self.__evolution.save_genome_to_file(RobotController.BEST_INDIVIDUAL_DATA_FILE, scores.index(max(scores)))
        self.__evolution.evolve(scores)
        self.__evolution.print_stats()
        if not os.path.exists(os.path.dirname(RoomSimulation.__DATA_FILE)):
            os.makedirs(os.path.dirname(RoomSimulation.__DATA_FILE))
        self.__evolution.save_to_file(RoomSimulation.__DATA_FILE)

        for robot in self.__robots:
            robot.respawn()

    def __calculate_robot_path_distance(self, robot: Robot):
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
            self.__network_visualization_widgets = [
                Rect(
                    pos=(WorkbenchView.VIEW_SIZE // 2, WorkbenchView.VIEW_SIZE + WorkbenchView.VISUALISATION_SIZE // 2),
                    size=(WorkbenchView.VIEW_SIZE, WorkbenchView.VISUALISATION_SIZE),
                    # background_color=(56, 50, 38)
                    background_color=(56, 50, 38)
                )
            ]
            species_groups = self.__evolution.get_population_grouped_by_species()
            horizontal_cells = ceil(sqrt(len(species_groups)))
            vertical_cells = ceil(len(species_groups) / horizontal_cells)
            cell_width = 1 / horizontal_cells
            cell_height = 1 / vertical_cells
            enum = enumerate(sorted(species_groups.values(), key=lambda ind: ind[0].species_id))
            for i, species_individuals in enum:
                x_i = i % horizontal_cells
                y_i = i // horizontal_cells
                self.__network_visualization_widgets.extend(
                    visualize_network(species_individuals[0].genome, cell_width * x_i, cell_height * y_i, cell_width,
                                      cell_height)
                )
            # self.__network_visualization_widgets.extend(visualize_network(self.__evolution.individuals[0].genome))
            if self._is_running:
                self._gui.add_widgets(tuple(self.__network_visualization_widgets))
