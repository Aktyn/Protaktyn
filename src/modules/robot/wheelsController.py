import RPi.GPIO as GPIO


class WheelsController:
    # Pins setup
    __in_left_forward = 24
    __in_left_backward = 23
    __in_right_forward = 5
    __in_right_backward = 6
    __en1 = 25
    __en2 = 26

    class Wheel:
        LEFT = 0
        RIGHT = 1

    class WheelState:
        STOPPED = 0
        FORWARD = 1
        BACKWARD = -1

    def __init__(self):
        self.__started = False

        self.__pin_states = {
            self.__in_left_forward: GPIO.LOW,
            self.__in_left_backward: GPIO.LOW,
            self.__in_right_forward: GPIO.LOW,
            self.__in_right_backward: GPIO.LOW,
        }

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.__in_left_forward, GPIO.OUT)
        GPIO.setup(self.__in_left_backward, GPIO.OUT)
        GPIO.setup(self.__en1, GPIO.OUT)
        GPIO.output(self.__in_left_forward, GPIO.LOW)
        GPIO.output(self.__in_left_backward, GPIO.LOW)

        GPIO.setup(self.__in_right_forward, GPIO.OUT)
        GPIO.setup(self.__in_right_backward, GPIO.OUT)
        GPIO.setup(self.__en2, GPIO.OUT)
        GPIO.output(self.__in_right_forward, GPIO.LOW)
        GPIO.output(self.__in_right_backward, GPIO.LOW)

        self.__p1 = GPIO.PWM(self.__en1, 1000)
        self.__p2 = GPIO.PWM(self.__en2, 1000)

    def __del__(self):
        self.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.STOPPED)
        self.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.STOPPED)
        GPIO.cleanup()

    def __start(self):
        # TODO:  allow speed change with eg.: self.__p1.ChangeDutyCycle(50)
        self.__p1.start(100)
        self.__p2.start(100)
        self.__started = True

    def __get_wheel_pins(self, wheel: int):
        if wheel == WheelsController.Wheel.LEFT:
            return [self.__in_left_forward, self.__in_left_backward]
        elif wheel == WheelsController.Wheel.RIGHT:
            return [self.__in_right_forward, self.__in_right_backward]
        raise ValueError("Invalid wheel")

    def __change_pin_state(self, pin: int, state: int):
        if self.__pin_states[pin] == state:
            return
        GPIO.output(pin, state)
        self.__pin_states[pin] = state

    def set_wheel_state(self, wheel: int, state: int):
        try:
            if not self.__started:
                self.__start()

            [forward_pin, backward_pin] = self.__get_wheel_pins(wheel)

            if state == WheelsController.WheelState.STOPPED:
                self.__change_pin_state(forward_pin, GPIO.LOW)
                self.__change_pin_state(backward_pin, GPIO.LOW)
            elif state == WheelsController.WheelState.FORWARD:
                self.__change_pin_state(forward_pin, GPIO.HIGH)
                self.__change_pin_state(backward_pin, GPIO.LOW)
            elif state == WheelsController.WheelState.BACKWARD:
                self.__change_pin_state(forward_pin, GPIO.LOW)
                self.__change_pin_state(backward_pin, GPIO.HIGH)

        except ValueError as e:
            print(e)
            return

    def stop_wheels(self):
        self.set_wheel_state(WheelsController.Wheel.LEFT, WheelsController.WheelState.STOPPED)
        self.set_wheel_state(WheelsController.Wheel.RIGHT, WheelsController.WheelState.STOPPED)
