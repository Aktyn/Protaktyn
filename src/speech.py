import time
from threading import Thread
from typing import Optional, Callable
import speech_recognition as sr


class Speech:
    # LISTENING_TIMEOUT = 300
    # PHRASE_TIME_LIMIT = 30
    __LANG = "pl-PL"  # "en-US", "pl-PL"
    __MAX_SAMPLES = 5
    __MAX_QUEUE_SAMPLES_SIZE = 8
    __AMBIENT_NOISE_ADJUSTING_DURATION = 0  # Restore 5 seconds on production

    class __Recorder:
        __SAMPLE_DURATION = 1.5

        def __init__(self, recognizer: sr.Recognizer, microphone: sr.Microphone):
            self.__running = False
            self.__recording_process: Optional[Thread] = None
            self.__recognizer = recognizer
            self.__microphone = microphone
            self.__samples: list[sr.AudioData] = []

        def adjust(self, duration: int):
            print("Adjusting ambient noise...")
            self.__recognizer.adjust_for_ambient_noise(self.__microphone, duration)
            print("Adjusted")

        def start(self):
            self.__running = True
            self.__recording_process = Thread(target=self.__recording_procedure)  # , args=(recognizer, microphone))
            self.__recording_process.daemon = True
            self.__recording_process.start()

        def stop(self):
            self.__running = False
            self.__recording_process.join()

        def __recording_procedure(self):
            while self.__running:
                sample = self.__recognizer.record(self.__microphone, self.__SAMPLE_DURATION)
                self.__samples.append(sample)

        def get_next_sample(self) -> sr.AudioData:
            while len(self.__samples) == 0:
                time.sleep(1 / 60)
                pass
            return self.__samples.pop(0)

        def get_queue_size(self):
            return len(self.__samples)

    def __init__(self, on_prediction_result: Callable[[int, dict, bool, int], None]):
        self.__on_prediction_result = on_prediction_result
        self.__running = False
        self.__recorder: Optional[Speech.__Recorder] = None

    @staticmethod
    def __get_prediction(recognizer: sr.Recognizer, samples: list[sr.AudioData]) -> Optional[dict]:
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
            return recognizer.recognize_google(combined, None, Speech.__LANG, show_all=True)
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

    def start(self):
        self.__running = True

        recognizer = sr.Recognizer()
        with sr.Microphone() as microphone:
            previous_sample: Optional[sr.AudioData] = None
            predictions_streak: list[sr.AudioData] = []
            prediction_id = 0
            self.__recorder = self.__Recorder(recognizer, microphone)
            self.__recorder.adjust(self.__AMBIENT_NOISE_ADJUSTING_DURATION)
            self.__recorder.start()

            while self.__running:
                sample = self.__recorder.get_next_sample()
                interim_prediction = self.__get_prediction(recognizer, [sample])

                if interim_prediction is None or len(interim_prediction) == 0 or len(
                        predictions_streak) >= self.__MAX_SAMPLES:
                    if len(predictions_streak) > 0:
                        predictions_streak.append(sample)
                        final_prediction = self.__get_prediction(recognizer, predictions_streak)
                        if final_prediction is not None:
                            self.__on_prediction_result(prediction_id, final_prediction, True, len(predictions_streak))
                        else:
                            print("Cannot compute final prediction")

                        prediction_id += 1
                        predictions_streak.clear()

                else:
                    printed = False
                    if len(predictions_streak) == 0:
                        printed = True
                        self.__on_prediction_result(prediction_id, interim_prediction, False, 1)
                        if previous_sample is not None:
                            predictions_streak.append(previous_sample)

                    predictions_streak.append(sample)

                    if not printed:
                        if self.__recorder and self.__recorder.get_queue_size() > self.__MAX_QUEUE_SAMPLES_SIZE:
                            print("Queue size is too big. Skipping combined interim prediction")
                            self.__on_prediction_result(prediction_id, interim_prediction, False, 1)
                        else:
                            combined_interim_prediction = self.__get_prediction(recognizer, predictions_streak)
                            if combined_interim_prediction is not None:
                                self.__on_prediction_result(prediction_id, combined_interim_prediction, False,
                                                            len(predictions_streak))

                previous_sample = sample

    def stop(self):
        if self.__recorder is not None:
            self.__recorder.stop()
            self.__recorder = None
        self.__running = False
