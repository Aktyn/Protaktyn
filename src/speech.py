from typing import Optional, Callable
import speech_recognition as sr

LANG = "en-US"  # "en-US", "pl-PL"
SAMPLE_DURATION = 1.5
MAX_SAMPLES = 5
AMBIENT_NOISE_ADJUSTING_DURATION = 5


# LISTENING_TIMEOUT = 300
# PHRASE_TIME_LIMIT = 30


def get_prediction(recognizer: sr.Recognizer, samples: list[sr.AudioData]) -> Optional[dict]:
    def combine_samples(samples_to_combine: list[sr.AudioData]) -> Optional[sr.AudioData]:
        if len(samples_to_combine) == 0:
            return None

        raw = bytes()
        for sample in samples_to_combine:
            raw += sample.get_raw_data()
        return sr.AudioData(raw, samples_to_combine[0].sample_rate, samples_to_combine[0].sample_width)

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
        return recognizer.recognize_google(combined, None, LANG, show_all=True)
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def start_listening(on_prediction_result: Callable[[int, dict, bool], None]):
    recognizer = sr.Recognizer()
    with sr.Microphone() as microphone:
        print("Adjusting ambient noise...")
        recognizer.adjust_for_ambient_noise(microphone, duration=AMBIENT_NOISE_ADJUSTING_DURATION)
        print("Adjusted")
        previous_sample: Optional[sr.AudioData] = None
        predictions_streak: list[sr.AudioData] = []
        prediction_id = 0
        while True:
            # TODO: separate recording and processing by threads
            sample = recognizer.record(microphone, SAMPLE_DURATION)
            interim_prediction = get_prediction(recognizer, [sample])

            if interim_prediction is None or len(predictions_streak) >= MAX_SAMPLES:
                if len(predictions_streak) > 0:
                    predictions_streak.append(sample)
                    final_prediction = get_prediction(recognizer, predictions_streak)
                    if final_prediction is not None:
                        on_prediction_result(prediction_id, final_prediction, True)
                    else:
                        print("Cannot compute final prediction")

                    prediction_id += 1
                    predictions_streak.clear()

            else:
                printed = False
                if len(predictions_streak) == 0:
                    # print("Interim prediction: " + interim_prediction)
                    printed = True
                    on_prediction_result(prediction_id, interim_prediction, False)
                    if previous_sample is not None:
                        predictions_streak.append(previous_sample)

                predictions_streak.append(sample)

                if not printed:
                    # combined_interim_prediction = get_prediction(recognizer, predictions_streak)
                    # if combined_interim_prediction is not None:
                    #     on_prediction_result(prediction_id, combined_interim_prediction, False)
                    # !Optimized for now due to combining predictions takes too long to compute
                    on_prediction_result(prediction_id, interim_prediction, False)

            previous_sample = sample
