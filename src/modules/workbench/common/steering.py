class Steering:
    def __init__(self):
        self.FORWARD = False
        self.BACKWARD = False
        self.LEFT = False
        self.RIGHT = False


class KeyboardSteering(Steering):
    def __init__(self):
        import pynput
        super().__init__()
        self.__listener = pynput.keyboard.Listener(on_press=lambda key: self.__on_press(key, True),
                                                   on_release=lambda key: self.__on_press(key, False))
        self.__listener.start()

    def close(self):
        self.__listener.stop()

    def __on_press(self, key, toggle: bool):
        # noinspection PyBroadException
        try:
            k = key.char
        except BaseException:
            k = key.name

        if k == 'w' or k == 'up':
            self.FORWARD = toggle
        elif k == 's' or k == 'down':
            self.BACKWARD = toggle
        elif k == 'a' or k == 'left':
            self.LEFT = toggle
        elif k == 'd' or k == 'right':
            self.RIGHT = toggle
