import re
from typing import Match, Optional
from src.config.commands import Commands
from src.epaper.epaper import EPaper
from src.gui.core.gui import GUI
from src.modules.moduleBase import ModuleBase
from src.common.utils import loud_print, get_argument_value
from src.modules.scoreboard.view import ScoreboardView


class ScoreboardModule(ModuleBase):
    def __init__(self, gui: GUI):
        super().__init__(gui)

        self.__view = ScoreboardView(on_left_player_point=lambda: self.__handle_point_increase(1, 0),
                                     on_right_player_point=lambda: self.__handle_point_increase(0, 1))
        self._gui.set_view(self.__view)

        self.__epaper = EPaper()
        self.__points = (0, 0)
        self.__set_points = (0, 0)

        self.__update_points(0, 0)
        self.__current_set_points_prediction_id: Optional[int] = None
        self.__set_points_match_results: list[dict] = []

        self.__points_for_left_player_prediction_id: Optional[int] = None
        self.__points_for_right_player_prediction_id: Optional[int] = None
        self.__point_for_left_player_results: list[dict] = []
        self.__point_for_right_player_results: list[dict] = []

        super().register_command(Commands.SCOREBOARD.reset, self.__handle_reset)
        super().register_command(Commands.SCOREBOARD.set_points, self.__handle_set_points_interim,
                                 self.__handle_set_points_finalize)
        super().register_command(Commands.SCOREBOARD.point_for_left_player,
                                 lambda _, __, ___: self.__handle_point_increase_interim(1, 0, _, __, ___),
                                 lambda _: self.__handle_point_increase_finalize(1, 0, _))
        super().register_command(Commands.SCOREBOARD.point_for_right_player,
                                 lambda _, __, ___: self.__handle_point_increase_interim(0, 1, _, __, ___),
                                 lambda _: self.__handle_point_increase_finalize(0, 1, _))

        super().register_command(Commands.SCOREBOARD.easter_egg, self.__handle_easter)

    def close(self):
        super().close()
        self.__epaper.close()

    def __handle_point_increase_interim(self, left: int, right: int, _match: Match[str], prediction_id: int,
                                        final: bool):
        if left > 0:
            if self.__points_for_left_player_prediction_id != prediction_id:
                self.__points_for_left_player_prediction_id = prediction_id
                self.__point_for_left_player_results = []

            self.__point_for_left_player_results.append(dict({
                "prediction_id": prediction_id,
                "final": final,
            }))
        if right > 0:
            if self.__points_for_right_player_prediction_id != prediction_id:
                self.__points_for_right_player_prediction_id = prediction_id
                self.__point_for_right_player_results = []

            self.__point_for_right_player_results.append(dict({
                "prediction_id": prediction_id,
                "final": final,
            }))

    def __handle_point_increase_finalize(self, left: int, right: int, prediction_id: int):
        for final in (True, False):
            if left > 0 and self.__points_for_left_player_prediction_id == prediction_id:
                for result in self.__point_for_left_player_results:
                    if result["final"] != final:
                        continue
                    self.__handle_point_increase(left, 0)
                    return
            if right > 0 and self.__points_for_right_player_prediction_id == prediction_id:
                for result in self.__point_for_right_player_results:
                    if result["final"] != final:
                        continue
                    self.__handle_point_increase(0, right)
                    return

    def __handle_point_increase(self, left: int, right: int):
        new_left_points = self.__points[0] + left
        new_right_points = self.__points[1] + right
        if new_left_points >= 11 and new_left_points - 2 >= new_right_points:
            new_left_points = new_right_points = 0
            self.__update_set_points(self.__set_points[0] + 1, self.__set_points[1])
        elif new_right_points >= 11 and new_right_points - 2 >= new_left_points:
            new_left_points = new_right_points = 0
            self.__update_set_points(self.__set_points[0], self.__set_points[1] + 1)

        self.__update_points(new_left_points, new_right_points)

    def __update_points(self, p1: int, p2: int):
        self.__points = (p1, p2)
        self.__view.update_points(p1, p2)
        self.__epaper.update_points(p1, p2)

    def __update_set_points(self, p1: int, p2: int):
        self.__set_points = (p1, p2)
        self.__view.update_set_points(p1, p2)
        self.__epaper.update_set_points(p1, p2)

    def __handle_reset(self, *_args):
        loud_print("Resetting scoreboard")
        self.__update_points(0, 0)

    def __handle_set_points_interim(self, match: Match[str], prediction_id: int, final: bool):
        groups = match.groups()
        if len(groups) < 4:
            return

        val1 = self.__parse_speach_number(groups[1])
        val2 = self.__parse_speach_number(groups[3])

        if val1 is None or val2 is None:
            return

        sets_point = match.string.find("setach") != -1

        if self.__current_set_points_prediction_id != prediction_id:
            self.__current_set_points_prediction_id = prediction_id
            self.__set_points_match_results = []
        self.__set_points_match_results.append(dict({
            "prediction_id": prediction_id,
            "final": final,
            "sets_point": sets_point,
            "val1": val1,
            "val2": val2
        }))

    def __handle_set_points_finalize(self, prediction_id: int):
        if self.__current_set_points_prediction_id != prediction_id:
            return

        sets_point = False
        for result in self.__set_points_match_results:
            if result["prediction_id"] != prediction_id:
                continue
            if result["sets_point"]:
                sets_point = True
                break

        # Deal with final results first
        for final in (True, False):
            for result in self.__set_points_match_results:
                if result["final"] != final:
                    continue

                # NOTE that results should be sorted by most accurate first. Otherwise, it should be sorted here
                if sets_point:
                    self.__update_set_points(result["val1"], result["val2"])
                else:
                    self.__update_points(result["val1"], result["val2"])
                return

    def __handle_easter(self, *_args):
        easter_text = get_argument_value("easter-text")
        if easter_text:
            self.__epaper.display_text(easter_text.replace("\\n", "\n"))

    @staticmethod
    def __parse_speach_number(word: str):
        if re.match(r"zer[oa]", word, re.IGNORECASE):
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
        else:
            try:
                digits = re.match(r"(\d+)", word)
                if digits is not None:
                    return int(digits.group(0))
            except ValueError:
                return None
        # TODO: handle bigger numbers
        return None
