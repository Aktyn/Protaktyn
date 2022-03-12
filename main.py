"""
Speech recognition test for raspberry pi

sudo apt install flac
sudo pip3 install speechrecognition
"""

from multiprocessing import Process
import sys
import time
import speech_recognition as sr


RECORD_DURATION = 3

def get_predictions(recognizer, microphone):
    """Get speech predictions of few seconds recording

    Args:
        r (Recognizer): Recognizer instance
        m (Microphone): Microphone instance
    """
    # print("Speak now")
    # a.adjust_for_ambient_noise(source, duration=5)
    # print("Adjusted for ambient noise")
    # audio = a.listen(source, 5, 0)
    audio = recognizer.record(microphone, RECORD_DURATION)
    try:
        data = recognizer.recognize_google(audio, None, "en-US", True)
        return data
    except sr.UnknownValueError:
        print("Cannot recognize speech command")
        return None

def start_reporting():
    """ TODO """
    recognizer = sr.Recognizer()
    with sr.Microphone() as microphone:
        while True:
            predictions = get_predictions(recognizer, microphone)
            if predictions is not None and not isinstance(predictions, list):
                print(predictions["alternative"])
                for result in predictions["alternative"]:
                    transcript = result["transcript"].lower()
                    if transcript == "stop":
                        sys.exit("Quiting program ")

proc1 = Process(target=start_reporting) #, args=(recognizer, microphone))
proc1.start()

proc2 = Process(target=start_reporting)
time.sleep(RECORD_DURATION / 2)
proc2.start()
