import re
import sys
from typing import Optional
from src.commandsInterface import CommandsInterface
from src.config.commands import Commands
from src.gui.core.gui import GUI
from src.gui.core.gui_consts import GUIConsts
from src.modules.moduleBase import ModuleBase
from src.modules.robot.module import RobotModule
from src.modules.scoreboard.module import ScoreboardModule
from src.speech import Speech
from src.common.utils import loud_print


class Core(CommandsInterface):

    def __init__(self):
        super().__init__(GUI(lambda: self.__handle_exit()))

        self.__module: Optional[ModuleBase] = None
        self.__last_prediction: Optional[str] = None

        # TODO: Help command displaying all available commands at the moment and specific help commands for each module

        super().register_command(regex=Commands.exit, on_match=self.__handle_exit_command)
        super().register_command(regex=Commands.SCOREBOARD.start_module,
                                 on_match=lambda *_args: self.__start_module(ScoreboardModule))
        super().register_command(regex=Commands.ROBOT.start_module,
                                 on_match=lambda *_args: self.__start_module(RobotModule))
        super().register_command(regex=Commands.exit_current_module, on_match=self.__exit_current_module)

        # noinspection PyBroadException
        try:
            for arg in sys.argv:
                if arg.startswith("start-module="):
                    module_name = re.match(r'^"?([^"]*)"?$', arg.split("=")[1]).group(0).lower()
                    if module_name == 'scoreboard':
                        self.__start_module(ScoreboardModule)
                    elif module_name == 'robot':
                        self.__start_module(RobotModule)
        except BaseException as e:
            print(e)

        self.__speech = Speech(on_prediction_result=self.__handle_prediction)
        try:
            self.__speech.start()
        except OSError as e:
            print(f"Failed to start speech recognition: {e}")

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
                self.__module.handle_command(text=transcript, prediction_id=prediction_id, is_final=final)

            self.handle_command(text=transcript, prediction_id=prediction_id, is_final=final)
        if final:
            if self.__module is not None:
                self.__module.handle_command_finalized(prediction_id)
            self.handle_command_finalized(prediction_id)

    def __exit_current_module(self, *_args):
        if self.__module is None:
            print("No module is currently running")
            return

        loud_print("Closing module: " + self.__module.__class__.__name__, True)
        self.__module.close()
        del self.__module
        self.__module = None

        self._gui.clear_view()
        self._gui.set_title(GUIConsts.WINDOW_TITLE)

    # noinspection PyPep8Naming
    def __start_module(self, ModuleClass: type(ModuleBase)):
        if self.__module is not None:
            if self.__module.__class__.__name__ == ModuleClass.__name__:
                return
            self.__exit_current_module(None)

        loud_print("Running module: " + ModuleClass.__name__, True)
        self.__module = ModuleClass(self._gui)

        self._gui.set_title(GUIConsts.WINDOW_TITLE + ' | ' + (
            self.__module.__class__.__name__ if self.__module is not None else 'None'))

    def __handle_exit_command(self, *_args):
        loud_print("Are you sure you want to exit?", True)
        super().register_confirmation_request(Commands.confirm, Commands.reject, self.__handle_exit, self.__abort_exit)

    @staticmethod
    def __abort_exit():
        loud_print("Exit aborted", True)

    def __handle_exit(self):
        loud_print("Exiting program")
        self.__exit_current_module()
        if self.__speech is not None:
            self.__speech.stop()
            self.__speech = None
        self._gui.close()
        super().close()
        # sys.exit(0)
