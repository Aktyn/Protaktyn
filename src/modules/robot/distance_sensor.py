import time

import RPi.GPIO as GPIO


class DistanceSensor:
    RANGE_CM = 200

    def __init__(self, trig: int, echo: int):
        self.__TRIG = trig
        self.__ECHO = echo

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.__TRIG, GPIO.OUT)
        GPIO.setup(self.__ECHO, GPIO.IN)
        GPIO.output(self.__TRIG, False)

    def get_distance(self):
        """
        Returns: distance in cm
        """
        GPIO.output(self.__TRIG, True)
        time.sleep(0.00001)
        GPIO.output(self.__TRIG, False)

        pulse_start: float = 0
        pulse_end: float = 0
        while GPIO.input(self.__ECHO) == 0:
            pulse_start = time.time()
        while GPIO.input(self.__ECHO) == 1:
            pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start
        return pulse_duration * 17150
