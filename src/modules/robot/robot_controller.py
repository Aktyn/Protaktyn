import json
import math
import os

from enum import Enum
from time import time
from typing import Optional
from src.common.common_utils import data_dir
from src.modules.workbench.neural_network.network import NeuralNetwork


class RobotController:
    class Direction(Enum):
        FORWARD, BACKWARD, LEFT, RIGHT = range(4)

    class __MovementProcedure:
        def __init__(self, direction: 'RobotController.Direction', duration: float):
            self.direction = direction
            self.duration = duration

    BEST_INDIVIDUAL_DATA_FILE = os.path.join(data_dir, 'room_best_individual.json')
    __STEERING_THRESHOLD = 1 / 3
    __FULL_CIRCLE_ROTATION_DURATION = 2.6667
    VIEW_ANGLE = math.pi * 0.5  # Should match the camera view angle
    MOVEMENT_SPEED = 0.5  # Robot movement speed in meters per second
    __FRONT_SENSOR_OBSTACLE_THRESHOLD = 0.9
    __SIDE_SENSOR_OBSTACLE_THRESHOLD = 0.7
    __OBSTACLE_RETREAT_DURATION = 1.0
    __OBSTACLE_RETREAT_ROTATION_FACTOR = 0.05

    def __init__(self):
        self.__network = RobotController.load_best_ai_player()
        self.__last_update_time: Optional[float] = None

        # For turning
        self.__rotation_procedure: Optional[RobotController.__MovementProcedure] = None

        # For moving forward or backward
        self.__movement_procedure: Optional[RobotController.__MovementProcedure] = None

    @staticmethod
    def load_best_ai_player():
        if not os.path.isfile(RobotController.BEST_INDIVIDUAL_DATA_FILE):
            return None
        f = open(RobotController.BEST_INDIVIDUAL_DATA_FILE, "r")
        data = json.load(f)
        f.close()

        return NeuralNetwork.from_dict(data)

    def update(self, sensors: list[float], estimated_cat_position: Optional[dict[str, float]]) -> dict[Direction, bool]:
        """
        Calculate the robot's current movement according to some inputs
        Args:
            sensors: list of normalized distance sensors values [front, left, right]
            estimated_cat_position: dictionary with key 'x' representing the cat's normalized x coordinate relative to camera view and key 'distance' representing estimated distance (in meters) of the cat from the robot

        Returns:
            A dictionary with RobotController.Direction as keys and boolean values
        """

        now = time()
        if self.__last_update_time is None:
            self.__last_update_time = now
        delta_time = now - self.__last_update_time
        self.__last_update_time = now

        if estimated_cat_position is not None:
            self.__rotation_procedure = RobotController.__MovementProcedure(
                RobotController.Direction.LEFT if estimated_cat_position['x'] > 0 else RobotController.Direction.RIGHT,
                (
                        abs(estimated_cat_position['x']) * (RobotController.VIEW_ANGLE / 2.0) / (math.pi * 2.0)
                ) * RobotController.__FULL_CIRCLE_ROTATION_DURATION
            )
            self.__movement_procedure = RobotController.__MovementProcedure(
                RobotController.Direction.FORWARD,
                estimated_cat_position['distance'] / RobotController.MOVEMENT_SPEED
            )

        # Move back a bit if front sensor is detecting near obstacle
        if sensors[0] > RobotController.__FRONT_SENSOR_OBSTACLE_THRESHOLD:
            self.__movement_procedure = RobotController.__MovementProcedure(
                RobotController.Direction.BACKWARD,
                RobotController.__OBSTACLE_RETREAT_DURATION
            )

            # Rotate a bit if obstacle is detected by the left or right sensor
            if sensors[1] > RobotController.__SIDE_SENSOR_OBSTACLE_THRESHOLD:  # Left sensor
                self.__rotation_procedure = RobotController.__MovementProcedure(
                    RobotController.Direction.RIGHT,
                    RobotController.__FULL_CIRCLE_ROTATION_DURATION * RobotController.__OBSTACLE_RETREAT_ROTATION_FACTOR
                )
            if sensors[2] > RobotController.__SIDE_SENSOR_OBSTACLE_THRESHOLD:  # Right sensor
                self.__rotation_procedure = RobotController.__MovementProcedure(
                    RobotController.Direction.LEFT,
                    RobotController.__FULL_CIRCLE_ROTATION_DURATION * RobotController.__OBSTACLE_RETREAT_ROTATION_FACTOR
                )

        if self.__rotation_procedure is not None:
            print(f"Rotation procedure: {self.__rotation_procedure.direction} | {self.__rotation_procedure.duration}")
            self.__rotation_procedure.duration -= delta_time
            if self.__rotation_procedure.duration <= 0:
                self.__rotation_procedure = None
            else:
                return {
                    RobotController.Direction.FORWARD: False,
                    RobotController.Direction.BACKWARD: False,
                    RobotController.Direction.LEFT: self.__rotation_procedure.direction == RobotController.Direction.LEFT,
                    RobotController.Direction.RIGHT: self.__rotation_procedure.direction == RobotController.Direction.RIGHT
                }

        if self.__movement_procedure is not None:
            print(f"Movement procedure: {self.__movement_procedure.direction} | {self.__movement_procedure.duration}")
            self.__movement_procedure.duration -= delta_time
            if self.__movement_procedure.duration <= 0:
                self.__movement_procedure = None
            else:
                return {
                    RobotController.Direction.FORWARD: self.__movement_procedure.direction == RobotController.Direction.FORWARD,
                    RobotController.Direction.BACKWARD: self.__movement_procedure.direction == RobotController.Direction.BACKWARD,
                    RobotController.Direction.LEFT: False,
                    RobotController.Direction.RIGHT: False
                }

        prediction = self.__network.calculate(sensors)
        if len(prediction) != len(self.__network.layers[-1]):
            raise ValueError("Network output size does not match number of neurons in last layer of network")

        return {
            RobotController.Direction.FORWARD: prediction[0] > self.__STEERING_THRESHOLD,
            RobotController.Direction.BACKWARD: prediction[0] < -self.__STEERING_THRESHOLD,
            RobotController.Direction.LEFT: prediction[1] > self.__STEERING_THRESHOLD,
            RobotController.Direction.RIGHT: prediction[1] < -self.__STEERING_THRESHOLD
        }
