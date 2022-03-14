"""
Speech recognition test for raspberry pi

sudo apt install flac
sudo pip3 install speechrecognition
"""
from typing import Optional

from gtts import gTTS
from io import BytesIO

from pydub import AudioSegment
from pydub.playback import play
import sys
import re
import speech_recognition as sr

LANG = "pl-PL"  # "en-US"
SAMPLE_DURATION = 1.5
MAX_SAMPLES = 5
# LISTENING_TIMEOUT = 300
# PHRASE_TIME_LIMIT = 30
AMBIENT_NOISE_ADJUSTING_DURATION = 5


def combine_samples(samples):
    """ Combine multiple AudioData objects into one.
    Args:
        samples (list[sr.AudioData]): AudioData list
    Returns:
        Optional[sr.AudioData]
    """
    if len(samples) == 0:
        return None

    raw = bytes()
    for sample in samples:
        raw += sample.get_raw_data()
    return sr.AudioData(raw, samples[0].sample_rate, samples[0].sample_width)


def get_prediction(recognizer, samples, show_all):
    """Get speech predictions of few seconds recording

    Args:
        recognizer (sr.Recognizer): Recognizer instance
        samples (list[sr.AudioData]): AudioData list
        show_all (bool): Show all predictions
    Returns:
        str
    """

    # while True:
    #     try:
    #         audio = recognizer.listen(microphone, LISTENING_TIMEOUT, PHRASE_TIME_LIMIT)
    #         break
    #     except sr.WaitTimeoutError:
    #         return None
    if len(samples) == 0:
        return None
    try:
        combined = samples[0] if len(samples) == 1 else combine_samples(samples)
        if combined is None:
            return None
        data = recognizer.recognize_google(combined, None, LANG, show_all)
        return data
    except sr.UnknownValueError:
        return None


def start_listening():
    recognizer = sr.Recognizer()
    with sr.Microphone() as microphone:
        print("Adjusting ambient noise...")
        recognizer.adjust_for_ambient_noise(microphone, duration=AMBIENT_NOISE_ADJUSTING_DURATION)
        print("Adjusted")
        previous_sample: Optional[sr.AudioData] = None
        predictions_streak: list[sr.AudioData] = []
        while True:
            sample = recognizer.record(microphone, SAMPLE_DURATION)
            interim_prediction = get_prediction(recognizer, [sample], False)

            if interim_prediction is None or len(predictions_streak) >= MAX_SAMPLES:
                if len(predictions_streak) > 0:
                    predictions_streak.append(sample)
                    final_prediction = get_prediction(recognizer, predictions_streak, True)
                    if final_prediction is not None and not isinstance(final_prediction, list):
                        print(final_prediction)
                        for result in final_prediction["alternative"]:
                            handle_prediction(result["transcript"])
                    else:
                        print("[Cannot compute final prediction]")
                    predictions_streak.clear()

            else:
                printed = False
                if len(predictions_streak) == 0:
                    print("Interim prediction: " + interim_prediction)
                    printed = True
                    handle_prediction(interim_prediction)
                    if previous_sample is not None:
                        predictions_streak.append(previous_sample)
                predictions_streak.append(sample)

                if not printed:
                    # combined_interim_prediction = get_prediction(recognizer, predictions_streak, False)
                    # print("Interim prediction: " +
                    #       combined_interim_prediction if combined_interim_prediction is not None else "-")
                    # handle_prediction(combined_interim_prediction)
                    print("Interim prediction: " + interim_prediction)
                    handle_prediction(interim_prediction)

            previous_sample = sample
            # else

            # if predictions is not None and not isinstance(predictions, list):
            #     print(predictions["alternative"])
            #     for result in predictions["alternative"]:
            #         transcript = result["transcript"].lower()
            #         if transcript == "stop":
            #             speak("Quiting program")
            #             sys.exit("Quiting program ")
            # else:
            #     print("-")


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


def handle_prediction(prediction_text):
    """
     Args:
         prediction_text (str): Predicted text
         """
    if re.match(".*(koniec|zako[nń]cz|wy[lł][aą]cz).*", prediction_text, re.IGNORECASE):
        speak("Quiting program")
        sys.exit("Quiting program ")


start_listening()
