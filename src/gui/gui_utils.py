from typing import Callable


class MockPyQtSignal:
    def __init__(self):
        pass

    def connect(self, func: Callable):
        pass

    def emit(self, *args):
        pass
