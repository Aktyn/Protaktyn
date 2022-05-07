import re
from dataclasses import dataclass
from typing import Callable, Match, Optional
from src.common.utils import show_gui
from src.gui.core.gui import GUI
from src.gui.views.dialog import Dialog
from src.gui.views.view_base import ViewBase


@dataclass
class CommandSchema:
    regex: str
    on_match: Callable[[Match[str], int, bool], None]
    finalize: Optional[Callable[[int], None]] = None


class CommandsInterface:
    @dataclass
    class __Confirmation:
        accept_regex: str
        reject_regex: str
        on_confirm: Callable
        on_reject: Callable

    def __init__(self, gui: GUI):
        self._gui = gui
        self.__commands: list[CommandSchema] = []
        # None - no confirmation required, True - confirmed, False - rejected
        self.__waiting_confirmation: Optional[CommandsInterface.__Confirmation] = None
        self.__pre_confirmation_view: Optional[ViewBase] = None

    def close(self):
        self.__waiting_confirmation = None

    def is_awaiting_confirmation(self) -> bool:
        return self.__waiting_confirmation is not None

    def register_command(self, regex: str, on_match: Callable[[Match[str], int, bool], None],
                         on_finalize: Optional[Callable[[int], None]] = None):
        self.__commands.append(CommandSchema(regex, on_match, finalize=on_finalize))

    def handle_command(self, text: str, prediction_id: int, is_final: bool):
        if self.__waiting_confirmation:
            if re.match(self.__waiting_confirmation.accept_regex, text, re.IGNORECASE):
                self.__handle_confirmation_decision(True)
            elif re.match(self.__waiting_confirmation.reject_regex, text, re.IGNORECASE):
                self.__handle_confirmation_decision(False)
            return

        for command in self.__commands:
            match_result = re.match(command.regex, text, re.IGNORECASE)
            if match_result is not None:
                command.on_match(match_result, prediction_id, is_final)

    def handle_command_finalized(self, prediction_id: int):
        for command in self.__commands:
            if command.finalize is not None:
                command.finalize(prediction_id)

    def register_confirmation_request(self, accept_regex: str, reject_regex: str, on_confirm: Callable,
                                      on_reject: Callable):
        if self.__waiting_confirmation is not None:
            print("Confirmation request already exists")
            return

        self.__waiting_confirmation = self.__Confirmation(accept_regex, reject_regex, on_confirm, on_reject)

        if show_gui():
            self.__pre_confirmation_view = self._gui.get_view()
            self._gui.set_view(Dialog(on_confirm=lambda: self.__handle_confirmation_decision(True),
                                      on_reject=lambda: self.__handle_confirmation_decision(False)))

    def __handle_confirmation_decision(self, confirmed: bool):
        if self.__pre_confirmation_view is not None:
            self._gui.set_view(self.__pre_confirmation_view)
            self.__pre_confirmation_view = None
        else:
            self._gui.remove_all_widgets()

        if self.__waiting_confirmation is not None:
            if confirmed:
                callback = self.__waiting_confirmation.on_confirm
            else:
                callback = self.__waiting_confirmation.on_reject

            self.__waiting_confirmation = None
            callback()
