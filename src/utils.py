import re
import sys
from src.speaker import speak
from threading import Thread


# TODO: try and cache result
def show_gui():
    return "nogui" not in map(lambda arg: arg.lower(), sys.argv)


# TODO: same as above
def use_epaper():
    return "use-epaper" in map(lambda arg: arg.lower(), sys.argv)


# TODO: same as above
def disable_speaker():
    return "disable-speaker" in map(lambda arg: arg.lower(), sys.argv)


def get_argument_value(argument_name: str):
    for arg in sys.argv:
        match = re.match(rf"{argument_name}=(.*)", arg)
        if match and len(match.groups()) > 0:
            return match.groups()[0]
    return None


def loud_print(text: str, speak_asynchronously: bool = False):
    print(text)
    if disable_speaker():
        return
    if speak_asynchronously:
        speaking_thread = Thread(target=lambda _text: speak(_text), args=(text,))  # , args=(recognizer, microphone))
        speaking_thread.start()
    else:
        speak(text)
