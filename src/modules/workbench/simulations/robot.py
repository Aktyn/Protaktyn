from src.common.math_utils import mix
from src.modules.workbench.common.steering import Steering
from src.modules.workbench.simulations.physics_simulation_base import PhysicsSimulationBase
from math import cos, sin, pi, sqrt


class Robot:
    _SENSOR_RANGE = 2
    _RENDER_SENSORS = True
    _STUCK_DURATION = 5
    _STUCK_DISTANCE_THRESHOLD = 0.5
    _SAFE_DISTANCE_FROM_WALL = 0.10
    DEFAULT_COLOR = (255, 196, 128)

    def __init__(self, scale: float, steering: Steering = Steering(), pos=(0., 0.), can_stuck=True, render=True):
        self.__delta_timer = 0.0
        self.__arrived = False
        self.__arrived_time = 0.0
        self.__stuck = False
        self.__stuck_time = 0.0
        self.__can_stuck = can_stuck
        self.__last_position_check_timestamp = 0
        self.__last_position_check_position = (0., 0.)

        self.__moved_distance = 0.0
        self.__distance_record_time = 0.0
        self.__last_position = (0., 0.)

        self.steering = steering
        self.__scale = scale
        self.__movement_speed = 0.1
        self.__rotation_speed = pi * 0.75
        self.__box = PhysicsSimulationBase.Box(pos=pos,
                                               size=(0.15 * self.__scale, 0.3 * self.__scale),
                                               color=Robot.DEFAULT_COLOR, collision_type=0x0002, render=render)
        # Prevent from colliding with other robots
        self.__box.body.set_collision_filtering(categories=0x0002, mask=0xFFFFFFFF ^ 0x0002)
        for shape in self.__box.body.shapes:
            shape.friction = 0.99
            shape.elasticity = 0.01

        self.__sensor_color = (128, 255, 128)
        self.__active_sensor_color = (128, 128, 255)

        sensors_count = 3

        self.__proximity_sensors: list[PhysicsSimulationBase.Line] = list(
            map(lambda _: PhysicsSimulationBase.Line(pos_start=(0, 0), pos_end=(0, 0), color=self.__sensor_color,
                                                     render=render and Robot._RENDER_SENSORS),
                range(sensors_count))
        )
        self.__proximity_sensors_values = list(map(lambda _: 0., range(sensors_count)))
        self.__sensor_angles = [0, 0.25, -0.25]

    def __delta_now(self):
        return self.__delta_timer

    def objects(self):
        return *self.__proximity_sensors, self.__box

    def set_arrived(self):
        self.__arrived = True
        self.__arrived_time = self.__delta_timer
        self.__box.set_color((128, 255, 128))

    def set_color(self, color: tuple[int, int, int]):
        self.__box.set_color(color)

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
    def angle(self):
        return self.__box.body.angle

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

    @property
    def distance_record_time(self):
        return self.__distance_record_time

    def register_path_distance(self, distance: float):
        if distance > self.__moved_distance:
            self.__distance_record_time = self.__delta_timer
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
        self.__distance_record_time = 0.0
        self.__last_position = (0., 0.)

        self.__box.body.set_position((0., 0.))
        self.__box.body.set_angle(0)
        self.__box.body.set_velocity((0., 0.))
        self.__box.body.set_angular_velocity(0)

    def get_sensors_values(self):
        return self.__proximity_sensors_values

    def update(self, delta_time: float, simulation: PhysicsSimulationBase):
        self.__delta_timer += delta_time

        if self.__stuck or self.__arrived:
            return
        elif self.__can_stuck:
            dst_squared = (self.pos[0] - self.__last_position_check_position[0]) ** 2 + \
                          (self.pos[1] - self.__last_position_check_position[1]) ** 2
            if dst_squared > (Robot._STUCK_DISTANCE_THRESHOLD * self.__scale) ** 2:
                self.__last_position_check_position = (self.pos[0], self.pos[1])
                self.__last_position_check_timestamp = self.__delta_timer
            elif self.__delta_timer - self.__last_position_check_timestamp > Robot._STUCK_DURATION:
                self.__last_position_check_timestamp = self.__delta_timer
                self.__stuck = True
                self.__stuck_time = self.__delta_timer
                self.__box.set_color((197, 190, 176))

        self.__last_position = (self.pos[0], self.pos[1])

        # touching_wall = False
        for i, sensor in enumerate(self.__proximity_sensors):
            c = cos(self.angle + pi * 0.5 + pi * self.__sensor_angles[i])
            s = sin(self.angle + pi * 0.5 + pi * self.__sensor_angles[i])

            # offset_len = (self.__box.size[0 if i % 2 == 0 else 1] / 2.0)
            offset_len = 0 if i % 2 == 0 else (self.__box.size[0] / 2.0)
            # offset_len = 0.

            sensor.set_positions((
                c * offset_len + self.__box.pos[0],
                s * offset_len + self.__box.pos[1]
            ), (
                c * (offset_len + Robot._SENSOR_RANGE * self.__scale) + self.__box.pos[0],
                s * (offset_len + Robot._SENSOR_RANGE * self.__scale) + self.__box.pos[1]
            ))

            contact_point = simulation.ray_cast(from_point=sensor.pos, to_point=sensor.pos_end,
                                                mask=0xFFFFFFFF ^ (0x0002 | 0x0004 | 0x0008))
            if contact_point is not None:
                distance = sqrt((contact_point[0] - sensor.pos[0]) ** 2 + (contact_point[1] - sensor.pos[1]) ** 2)

                if self.__can_stuck and distance < Robot._SAFE_DISTANCE_FROM_WALL * self.__scale + \
                        (self.__box.size[0] / 2.0):
                    self.__stuck = True
                    self.__stuck_time = self.__delta_timer
                    self.__box.set_color((197, 190, 176))

                # if not touching_wall and distance < RoomSimulation._SAFE_DISTANCE_FROM_WALL * self.__scale + (
                #         self.__box.size[0] / 2.0):
                #     touching_wall = True

                normalized_distance = distance / (Robot._SENSOR_RANGE * self.__scale)
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
            # speed = self.__movement_speed if not touching_wall else self.__movement_speed * 0.2
            speed = self.__movement_speed
            # rotation_speed = self.__rotation_speed if not touching_wall else self.__rotation_speed * 0.2
            rotation_speed = self.__rotation_speed

            if self.steering.FORWARD:
                self.__box.body.set_velocity(
                    (cos(self.angle + pi / 2.0) * speed,
                     sin(self.angle + pi / 2.0) * speed)
                )
            if self.steering.BACKWARD:
                self.__box.body.set_velocity(
                    (cos(self.angle + pi / 2.0) * -speed,
                     sin(self.angle + pi / 2.0) * -speed)
                )
            if self.steering.LEFT:
                self.__box.body.set_angular_velocity(rotation_speed)
            if self.steering.RIGHT:
                self.__box.body.set_angular_velocity(-rotation_speed)
