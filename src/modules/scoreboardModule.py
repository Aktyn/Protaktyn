import re
from typing import Match

from src.config.commands import Commands
from src.gui.gui import GUIEvents
from src.modules.moduleBase import ModuleBase
from src.utils import loud_print


class ScoreboardModule(ModuleBase):
    def __init__(self, gui_events: GUIEvents):
        super().__init__(gui_events)

        self.__points = (0, 0)
        self.__update_points(0, 0)

        super().register_command(Commands.SCOREBOARD.reset, self.__handle_reset)
        super().register_command(Commands.SCOREBOARD.set_points, self.__handle_set_points)

    def close(self):
        self._gui_events.scoreboard_view_hide.emit()
        super().close()

    def __update_points(self, p1: int, p2: int):
        self.__points = (p1, p2)
        self._gui_events.scoreboard_view_update_points.emit(p1, p2)

    def __handle_reset(self, _):
        loud_print("Resetting scoreboard")
        self.__update_points(0, 0)

    def __handle_set_points(self, match: Match[str]):
        groups = match.groups()
        print("Groups:", groups)
        if len(groups) < 4:
            return

        val1 = self.__parse_speach_number(groups[1])
        val2 = self.__parse_speach_number(groups[3])

        if val1 is None or val2 is None:
            return

        self.__update_points(val1, val2)

    @staticmethod
    def __parse_speach_number(word: str):
        if re.match(r"\d+", word):
            return int(word)
        elif re.match(r"zer[oa]", word, re.IGNORECASE):
            return 0
        elif re.match(r"(jeden|jednego)", word, re.IGNORECASE):
            return 1
        elif re.match(r"(dwa|dwóch)", word, re.IGNORECASE):
            return 2
        elif re.match(r"(trzy|trzech)", word, re.IGNORECASE):
            return 3
        elif re.match(r"(cztery|czterech)", word, re.IGNORECASE):
            return 4
        elif re.match(r"(pięć|pięciu)", word, re.IGNORECASE):
            return 5
        elif re.match(r"(sześć|sześciu)", word, re.IGNORECASE):
            return 6
        elif re.match(r"(siedem|siedmiu)", word, re.IGNORECASE):
            return 7
        elif re.match(r"(osiem|ośmiu)", word, re.IGNORECASE):
            return 8
        elif re.match(r"dziewię[cć](iu)?", word, re.IGNORECASE):
            return 9
        elif re.match(r"dziesię[cć](iu)?", word, re.IGNORECASE):
            return 10
        elif re.match(r"(jedenaście|jedenastu)", word, re.IGNORECASE):
            return 11
        elif re.match(r"(dwanaście|dwunastu)", word, re.IGNORECASE):
            return 12
        elif re.match(r"(trzynaście|trzynastu)", word, re.IGNORECASE):
            return 13
        elif re.match(r"(czternaście|czternastu)", word, re.IGNORECASE):
            return 14
        elif re.match(r"(piętnaście|piętnastu)", word, re.IGNORECASE):
            return 15
        elif re.match(r"(szesnaście|szesnastu)", word, re.IGNORECASE):
            return 16
        elif re.match(r"(siedemnaście|siedemnastu)", word, re.IGNORECASE):
            return 17
        elif re.match(r"(osiemnaście|osiemnastu)", word, re.IGNORECASE):
            return 18
        elif re.match(r"(dziewiętnaście|dziewiętnastu)", word, re.IGNORECASE):
            return 19
        elif re.match(r"(dwadzieścia|dwudziestu)", word, re.IGNORECASE):
            return 20
        # TODO: handle bigger numbers
        return None
