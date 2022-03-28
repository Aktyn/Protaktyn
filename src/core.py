import sys
from typing import Optional
from src.commandsInterface import CommandsInterface
from src.config.commands import Commands
from src.gui.gui import GUI, GUIEvents
from src.modules.moduleBase import ModuleBase
from src.modules.scoreboardModule import ScoreboardModule
from src.speech import Speech
from src.utils import loud_print


class Core(CommandsInterface):

    def __init__(self):
        super().__init__()
        GUI(self.__start)

    def __start(self, gui_events: GUIEvents):
        self.__gui_events = gui_events
        self.__module: Optional[ModuleBase] = None
        self.__last_prediction: Optional[str] = None
        self.__update_gui_info_label()

        super().register_command(regex=Commands.exit, on_match=self.__handle_exit_command)
        super().register_command(regex=Commands.start_scoreboard_module,
                                 on_match=lambda _: self.__start_module(ScoreboardModule))
        super().register_command(regex=Commands.exit_current_module, on_match=self.__exit_current_module)

        speech = Speech(on_prediction_result=self.__handle_prediction)
        speech.start()

    def __update_gui_info_label(self):
        self.__gui_events.set_info_text.emit(
            f"Module: {self.__module.__class__.__name__ if self.__module is not None else 'None'}; Spoken text: \"{self.__last_prediction or '-'}\"")

    def __handle_prediction(self, prediction_id: int, prediction_results: dict, final: bool = False,
                            samples_count: int = 0):
        if len(prediction_results) == 0:
            return

        alternatives = (prediction_results or {"alternative": []})["alternative"]
        if len(alternatives) > 0:
            self.__last_prediction = alternatives[0]["transcript"]

        results_list_string = "\n".join(map(lambda res: f"\t{res['transcript']}", alternatives))
        print(
            f"{'Final' if final else 'Interim'} prediction id: {prediction_id}, samples: {samples_count}, final: {final}, results:\n{results_list_string}")
        for result in alternatives:
            transcript = result["transcript"]

            if self.__module is not None and not self.is_awaiting_confirmation():
                self.__module.handle_command(text=transcript)

            self.handle_command(text=transcript)

        self.__update_gui_info_label()

    def __exit_current_module(self, _):
        if self.__module is None:
            loud_print("No module is currently running")
            return

        loud_print("Closing module: " + self.__module.__class__.__name__)
        self.__module.close()
        self.__module = None
        self.__update_gui_info_label()

    # noinspection PyPep8Naming
    def __start_module(self, ModuleClass: type(ModuleBase)):
        if self.__module is not None:
            if self.__module.__class__.__name__ == ModuleClass.__name__:
                return
            del self.__module

        loud_print("Running module: " + ModuleClass.__name__, True)
        self.__module = ModuleClass(self.__gui_events)
        self.__update_gui_info_label()

    def __handle_exit_command(self, _):
        self.__gui_events.show_confirmation_info.emit("Are you sure you want to exit?")
        super().register_confirmation_request(Commands.confirm, Commands.reject, self.__handle_exit_confirmation,
                                              self.__abort_exit)

    def __abort_exit(self):
        print("Exit aborted")
        self.__gui_events.close_confirmation_info.emit()

    def __handle_exit_confirmation(self):
        self.__gui_events.close.emit()
        loud_print("Exiting program")
        sys.exit(0)
