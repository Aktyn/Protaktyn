import sys
import re
from src.gui import GUI, GUIEvents
from src.speaker import speak
from src.speech import Speech


class Core:

    def __init__(self):
        GUI(self.__start)

    def __start(self, gui_events: GUIEvents):
        gui_events.set_label_text.emit("Awaiting speech results...")
        self.__gui_events = gui_events
        self.__best_final_results: list[str] = []
        speech = Speech(on_prediction_result=self.__handle_prediction)
        speech.start()

    def __handle_prediction(self, prediction_id: int, prediction_results: dict, final: bool = False,
                            samples_count: int = 0):
        if len(prediction_results) == 0:
            return

        alternatives = (prediction_results or {"alternative": []})["alternative"]
        if len(alternatives) > 0:
            best = alternatives[0]["transcript"]

            if final:
                self.__best_final_results.append(f"[id: {prediction_id}] {best}")

            self.__gui_events.set_label_text.emit("Current result:\n\t" + best + "\nFinal results:\n" + "\n".join(
                map(lambda res: f"\t{res}", self.__best_final_results if self.__best_final_results else [])))

        print(
            f"{'Final' if final else 'Interim'} prediction id: {prediction_id}, samples: {samples_count}, final: {final}, results:")
        for result in alternatives:
            transcript = result["transcript"]
            print("\t" + transcript)
            if re.match(".*(koniec|zako[nń]cz|wy[lł][aą]cz).*", transcript, re.IGNORECASE):
                speak("Quiting program")
                sys.exit("Quiting program ")
