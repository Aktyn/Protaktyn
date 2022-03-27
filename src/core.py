import sys
import re
from src.gui import GUI, GUIEvents
from src.speaker import speak
from src.speech import start_listening


class Core:
    def __init__(self):
        GUI(self.__start)

    def __start(self, gui_events: GUIEvents):
        gui_events.set_label_text.emit("Listening...")
        self.__gui_events = gui_events
        start_listening(on_prediction_result=self.__handle_prediction)

    def __handle_prediction(self, prediction_id: int, prediction_results: dict, final: bool = False):
        if len(prediction_results) == 0:
            return

        alternatives = (prediction_results or {"alternative": []})["alternative"]
        if len(alternatives) > 0:
            self.__gui_events.set_label_text.emit("\n".join(map(lambda a: a["transcript"], alternatives)))

        print(f"{'Final' if final else 'Interim'} prediction id: {prediction_id}, final: {final}, results:")
        for result in alternatives:
            transcript = result["transcript"]
            print("\t" + transcript)
            if final and re.match(".*(koniec|zako[nń]cz|wy[lł][aą]cz).*", transcript, re.IGNORECASE):
                speak("Quiting program")
                sys.exit("Quiting program ")
