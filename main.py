"""
Speech recognition test for raspberry pi

sudo apt install flac
sudo pip3 install speechrecognition
"""

# from multiprocessing import Process
# import sys
# import time
from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr

# RECORD_DURATION = 3
LISTENING_TIMEOUT = 30
PHRASE_TIME_LIMIT = 10
AMBIENT_NOISE_ADJUSTING_DURATION = 5


def get_predictions(recognizer, microphone):
    """Get speech predictions of few seconds recording

    Args:
        recognizer (sr.Recognizer): Recognizer instance
        microphone (sr.Microphone): Microphone instance
    Returns:
        str
    """
    # print("Speak now")

    while True:
        try:
            audio = recognizer.listen(microphone, LISTENING_TIMEOUT, PHRASE_TIME_LIMIT)
            break
        except sr.WaitTimeoutError:
            return None
    # audio = recognizer.record(microphone, RECORD_DURATION)
    try:
        data = recognizer.recognize_google(audio, None, "en-US", False)
        return data
    except sr.UnknownValueError:
        return None


def start_reporting():
    recognizer = sr.Recognizer()
    with sr.Microphone() as microphone:
        recognizer.adjust_for_ambient_noise(microphone, duration=AMBIENT_NOISE_ADJUSTING_DURATION)
        print("Adjusted for ambient noise")
        while True:
            predictions = get_predictions(recognizer, microphone)
            # if predictions:
            print("[" + (predictions or "-") + "]")
            # if predictions is not None and not isinstance(predictions, list):
            #     print(predictions["alternative"])
            #     for result in predictions["alternative"]:
            #         transcript = result["transcript"].lower()
            #         if transcript == "stop":
            #             sys.exit("Quiting program ")


def speak(text):
    """
     Args:
         text (str): Text to speak
         """
    output = gTTS(text, lang='en', slow=False)
    fp = BytesIO()
    output.write_to_fp(fp)
    fp.seek(0)

    song = AudioSegment.from_file(fp, format="mp3")
    song -= 20  # decrease volume by 20 decibels
    play(song)


speak("Cabbage and acid")
start_reporting()

# proc_1 = Process(target=start_reporting)  # , args=(recognizer, microphone))
# proc_1.start()

# proc_2 = Process(target=start_reporting)
# time.sleep(RECORD_DURATION / 2)
# proc_2.start()
