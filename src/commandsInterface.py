import re
from dataclasses import dataclass
from typing import Callable, Match, Optional


@dataclass
class CommandSchema:
    regex: str
    on_match: Callable[[Match[str]], None]


class CommandsInterface:
    @dataclass
    class __Confirmation:
        accept_regex: str
        reject_regex: str
        on_confirm: Callable
        on_reject: Optional[Callable] = None

    def __init__(self):
        self.__commands: list[CommandSchema] = []
        # None - no confirmation required, True - confirmed, False - rejected
        self.__waiting_confirmation: Optional[CommandsInterface.__Confirmation] = None

    def is_awaiting_confirmation(self) -> bool:
        return self.__waiting_confirmation is not None

    def register_command(self, regex: str, on_match: Callable[[Match[str]], None]):
        self.__commands.append(CommandSchema(regex, on_match))

    def handle_command(self, text: str):
        if self.__waiting_confirmation:
            if re.match(self.__waiting_confirmation.accept_regex, text, re.IGNORECASE):
                on_confirm = self.__waiting_confirmation.on_confirm
                self.__waiting_confirmation = None
                on_confirm()
            elif re.match(self.__waiting_confirmation.reject_regex, text, re.IGNORECASE):
                on_reject = self.__waiting_confirmation.on_reject
                self.__waiting_confirmation = None
                if on_reject is not None:
                    on_reject()
            return

        for command in self.__commands:
            match_result = re.match(command.regex, text, re.IGNORECASE)
            if match_result is not None:
                command.on_match(match_result)

    def register_confirmation_request(self, accept_regex: str, reject_regex: str, on_confirm: Callable,
                                      on_reject: Optional[Callable] = None):
        self.__waiting_confirmation = self.__Confirmation(accept_regex, reject_regex, on_confirm, on_reject)

