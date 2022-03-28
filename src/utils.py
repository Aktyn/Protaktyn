from src.speaker import speak
from threading import Thread


def loud_print(text: str, speak_asynchronously: bool = False):
    print(text)
    if speak_asynchronously:
        speaking_thread = Thread(target=lambda _text: speak(_text), args=(text,))  # , args=(recognizer, microphone))
        speaking_thread.start()
    else:
        speak(text)
