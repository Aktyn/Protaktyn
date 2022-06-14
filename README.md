# Protaktyn
Repository for Raspberry Pi based multipurpose robot project

In order to test some parts of code you might need to create **RPi** directory with empty **\_\_init\_\_.py** file and **GPIO.py** with given content:
```python
LOW = 1
HIGH = 2
BCM = 1
IN = 1
OUT = 2


def setmode(_: int):
    pass


def setup(_: int, __: int):
    pass


def output(_: int, __: int):
    pass


def cleanup():
    pass


class PWM:
    def __init__(self, _: int, __: int):
        pass

    def start(self, _: int):
        pass
```
This is to mimic Raspberry Pi build-in GPIO library.