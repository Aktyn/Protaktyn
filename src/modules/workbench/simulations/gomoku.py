import json
import os
import time
from threading import Thread

from typing import Callable, Optional
from src.common.utils import data_dir
from src.gui.core.button import Button
from src.gui.core.gui import GUI
from src.gui.core.rect import Rect
from src.gui.core.widget import Widget
from src.modules.workbench.evolution.evolution import Evolution, EvolutionConfig
from src.modules.workbench.neural_network.network import NeuralNetwork
from src.modules.workbench.view import WorkbenchView


class GomokuSimulation:
    _BOARD_SIZE = 15  # 15
    _LINE_LENGTH_TO_WIN = 5  # 5
    _FIELD_MARGIN = 3
    _BOARD_TOP_OFFSET = 120
    _WHITE_COLOR = (255, 255, 255)
    _BLACK_COLOR = (0, 0, 0)

    __DATA_FILE = os.path.join(data_dir, 'gomoku_evolution.json')
    __BEST_INDIVIDUAL_DATA_FILE = os.path.join(data_dir, 'gomoku_best_individual.json')
    __POPULATION_SIZE = 200
    __LAYERS = [_BOARD_SIZE * _BOARD_SIZE, (_BOARD_SIZE * _BOARD_SIZE) * 2, _BOARD_SIZE * _BOARD_SIZE]

    class _FieldState:
        EMPTY = 0
        BLACK = -1
        WHITE = 1

    class _GomokuGame:
        def __init__(self, on_end: Callable[[int], None] = None):
            self.__on_end = on_end
            self.__finished = False

            self.__board = [[GomokuSimulation._FieldState.EMPTY for _ in range(GomokuSimulation._BOARD_SIZE)] for _ in
                            range(GomokuSimulation._BOARD_SIZE)]
            self.__player_turn = GomokuSimulation._FieldState.WHITE

        @property
        def board(self):
            return self.__board

        @property
        def finished(self):
            return self.__finished

        @property
        def player_turn(self):
            return self.__player_turn

        def __all_fields_filled(self):
            for row in self.__board:
                for field in row:
                    if field == GomokuSimulation._FieldState.EMPTY:
                        return False
            return True

        def __check_result(self, check_for_player: int) -> Optional[int]:
            def finish_game(draw=False):
                self.__finished = True
                result = GomokuSimulation._FieldState.EMPTY if draw else check_for_player
                if self.__on_end is not None:
                    self.__on_end(result)
                return result

            # Check if player won after his recent move
            for row_i in range(GomokuSimulation._BOARD_SIZE):
                for column_i in range(GomokuSimulation._BOARD_SIZE):
                    if self.__board[row_i][column_i] != check_for_player:
                        continue

                    # Check horizontal
                    if column_i + GomokuSimulation._LINE_LENGTH_TO_WIN <= GomokuSimulation._BOARD_SIZE:
                        for i in range(1, GomokuSimulation._LINE_LENGTH_TO_WIN):
                            if self.__board[row_i][column_i + i] != check_for_player:
                                break
                        else:
                            return finish_game()

                    # Check vertical
                    if row_i + GomokuSimulation._LINE_LENGTH_TO_WIN <= GomokuSimulation._BOARD_SIZE:
                        for i in range(1, GomokuSimulation._LINE_LENGTH_TO_WIN):
                            if self.__board[row_i + i][column_i] != check_for_player:
                                break
                        else:
                            return finish_game()

                    # Check diagonal up
                    if row_i + GomokuSimulation._LINE_LENGTH_TO_WIN <= GomokuSimulation._BOARD_SIZE and \
                            column_i + GomokuSimulation._LINE_LENGTH_TO_WIN <= GomokuSimulation._BOARD_SIZE:
                        for i in range(1, GomokuSimulation._LINE_LENGTH_TO_WIN):
                            if self.__board[row_i + i][column_i + i] != check_for_player:
                                break
                        else:
                            return finish_game()

                    # Check diagonal down
                    if row_i + GomokuSimulation._LINE_LENGTH_TO_WIN <= GomokuSimulation._BOARD_SIZE and \
                            column_i - GomokuSimulation._LINE_LENGTH_TO_WIN >= -1:
                        for i in range(1, GomokuSimulation._LINE_LENGTH_TO_WIN):
                            if self.__board[row_i + i][column_i - i] != check_for_player:
                                break
                        else:
                            return finish_game()

            # Check whether all fields are filled
            if self.__all_fields_filled():
                return finish_game(draw=True)

        def make_move(self, row_index: int, column_index: int):
            if self.__finished:
                return

            if self.__board[row_index][column_index] != GomokuSimulation._FieldState.EMPTY:
                return False

            self.__board[row_index][column_index] = self.__player_turn
            finish_result = self.__check_result(self.__player_turn)

            if finish_result is not None:
                return finish_result

            self.__player_turn = GomokuSimulation._FieldState.WHITE if self.__player_turn == GomokuSimulation._FieldState.BLACK \
                else GomokuSimulation._FieldState.BLACK

    def __init__(self, gui: GUI):
        self.__gui = gui
        self.__game = self.__start_test_game()
        self.__ai_player = self.__load_best_ai_player()
        self.__simulate = False
        self.__board_widgets: list[Widget] = []

        self.__render_board(self.__game)

        self.__simulation_thread: Optional[Thread] = None

    def close(self):
        self.__gui.remove_widgets(*self.__board_widgets)
        self.__board_widgets.clear()

        self.__simulate = False
        if self.__simulation_thread is not None:
            self.__simulation_thread.join()
            self.__simulation_thread = None

    def toggle_simulate(self, enable: bool):
        self.__simulate = enable
        if enable:
            self.__simulation_thread = Thread(target=self.__start_simulation, daemon=True)
            self.__simulation_thread.start()
        else:
            self.__simulation_thread.join()
            self.__simulation_thread = None
            self.__ai_player = self.__load_best_ai_player()

    @staticmethod
    def __load_best_ai_player():
        if not os.path.isfile(GomokuSimulation.__BEST_INDIVIDUAL_DATA_FILE):
            return None
        f = open(GomokuSimulation.__BEST_INDIVIDUAL_DATA_FILE, "r")
        data = json.load(f)
        f.close()

        return NeuralNetwork.from_dict(data)

    @staticmethod
    def __get_player_input(player: int, board: list[list[int]]):
        parsed_input: list[float] = []

        for row in board:
            parsed_input.extend(map(
                lambda field: 0.0 if field == GomokuSimulation._FieldState.EMPTY else (
                    1.0 if field == player else -1.0),
                row))

        return parsed_input

    @staticmethod
    def __get_move_from_prediction(prediction: list[float], board: list[list[int]]):
        # indexed: list[tuple[int, float]] = list(enumerate(prediction))
        indexed = filter(
            lambda el: board[el[0] // GomokuSimulation._BOARD_SIZE][
                           el[0] % GomokuSimulation._BOARD_SIZE] == GomokuSimulation._FieldState.EMPTY,
            zip(range(len(prediction)), prediction)
        )
        best_move_index: int = max(indexed, key=lambda el: el[1])[0]
        return best_move_index // GomokuSimulation._BOARD_SIZE, best_move_index % GomokuSimulation._BOARD_SIZE

    def __start_simulation(self):
        print(
            f"Generating population. It may take a while since there are {sum(GomokuSimulation.__LAYERS)} neurons and {GomokuSimulation.__LAYERS[0] * GomokuSimulation.__LAYERS[1] + GomokuSimulation.__LAYERS[1] * GomokuSimulation.__LAYERS[2]} connections to generate in each neural network")
        evolution = Evolution[NeuralNetwork](
            genomes=list(
                map(lambda _: NeuralNetwork(GomokuSimulation.__LAYERS, randomize_weights=True),
                    range(GomokuSimulation.__POPULATION_SIZE))),
            evolution_config=EvolutionConfig(
                elitism=8 / float(self.__POPULATION_SIZE),
                mutation_chance=0.05,
                mutation_scale=0.25,
                species_maturation_generations=40,
                maximum_species=6,
                species_creation_chance=0.1,
                species_extinction_chance=0.1
            )
        )
        print("Generating population done")
        if os.path.isfile(GomokuSimulation.__DATA_FILE):
            evolution.load_from_file(GomokuSimulation.__DATA_FILE)

        print("Starting simulation")
        while self.__simulate:
            scores: list[float] = list(map(lambda _: 0.0, range(GomokuSimulation.__POPULATION_SIZE)))

            # Make each AI player compete against every other AI player in the population and record their scores
            for i in range(GomokuSimulation.__POPULATION_SIZE):
                for j in range(i + 1, GomokuSimulation.__POPULATION_SIZE):
                    if not self.__simulate:
                        break

                    # print(f"Game of {i} and {j}")
                    player_i_network = evolution.individuals[i].genome  # type: NeuralNetwork
                    # player_i_color = GomokuSimulation._FieldState.WHITE if random() > 0.5 else GomokuSimulation._FieldState.BLACK
                    player_i_color = GomokuSimulation._FieldState.WHITE

                    player_j_network = evolution.individuals[j].genome  # type: NeuralNetwork
                    # player_j_color = GomokuSimulation._FieldState.WHITE if player_i_color == GomokuSimulation._FieldState.BLACK else GomokuSimulation._FieldState.BLACK
                    player_j_color = GomokuSimulation._FieldState.BLACK

                    game = GomokuSimulation._GomokuGame()
                    while not game.finished:
                        player_index, player_to_move, player_color_to_move = (i, player_i_network, player_i_color) \
                            if game.player_turn == player_i_color else (j, player_j_network, player_j_color)

                        player_input = self.__get_player_input(player_color_to_move, game.board)
                        if len(player_input) != GomokuSimulation.__LAYERS[0]:
                            raise Exception("Invalid input size")
                        prediction = player_to_move.calculate(player_input)
                        if len(prediction) != GomokuSimulation.__LAYERS[-1]:
                            raise ValueError(
                                "Network output size does not match number of neurons in last layer of network")

                        move = self.__get_move_from_prediction(prediction, game.board)
                        result = game.make_move(move[0], move[1])

                        if result is not None:
                            if result == GomokuSimulation._FieldState.EMPTY:
                                scores[player_index] += 1  # Point for draw
                            elif result == player_color_to_move:
                                scores[player_index] += 2  # 2 points for win

                            break

            # Saving best individual to separate file for later use
            evolution.save_genome_to_file(GomokuSimulation.__BEST_INDIVIDUAL_DATA_FILE, scores.index(max(scores)))
            evolution.evolve(scores)
            evolution.print_stats()
            if not os.path.exists(os.path.dirname(GomokuSimulation.__DATA_FILE)):
                os.makedirs(os.path.dirname(GomokuSimulation.__DATA_FILE))
            evolution.save_to_file(GomokuSimulation.__DATA_FILE)

            time.sleep(1.0 / 60.0)

    def __start_test_game(self):
        def on_game_finished(winner: int):
            print(
                f"Game over. {'Draw' if winner == GomokuSimulation._FieldState.EMPTY else 'Black player won' if winner == GomokuSimulation._FieldState.BLACK else 'White player won'}")
            self.__game = self.__start_test_game()

        return GomokuSimulation._GomokuGame(on_game_finished)

    def __on_field_click(self, row_index: int, col_index: int):
        if self.__ai_player is None:
            return

        self.__game.make_move(row_index, col_index)

        # Immediately make move for AI
        player_input = self.__get_player_input(GomokuSimulation._FieldState.BLACK, self.__game.board)
        prediction = self.__ai_player.calculate(player_input)
        move = self.__get_move_from_prediction(prediction, self.__game.board)
        self.__game.make_move(move[0], move[1])

        self.__render_board(self.__game)

    def __render_board(self, game: _GomokuGame):
        self.__gui.remove_widgets(*self.__board_widgets)
        self.__board_widgets.clear()

        field_size = WorkbenchView.VIEW_SIZE // GomokuSimulation._BOARD_SIZE

        for row_i, row in enumerate(game.board):
            for col_i, field in enumerate(row):
                pos = (
                    col_i * field_size + field_size // 2,
                    row_i * field_size + field_size // 2 + GomokuSimulation._BOARD_TOP_OFFSET
                )
                size = (
                    field_size - GomokuSimulation._FIELD_MARGIN,
                    field_size - GomokuSimulation._FIELD_MARGIN
                )

                if field == GomokuSimulation._FieldState.EMPTY:
                    empty_field = Button(text='', pos=pos, padding=0, on_click=lambda btn: self.__on_field_click(
                        self.__board_widgets.index(btn) // GomokuSimulation._BOARD_SIZE,
                        self.__board_widgets.index(btn) % GomokuSimulation._BOARD_SIZE
                    ))
                    empty_field.set_size(size)
                    self.__board_widgets.append(empty_field)
                else:
                    self.__board_widgets.append(Rect(
                        pos=pos,
                        size=size,
                        background_color=GomokuSimulation._WHITE_COLOR if field == GomokuSimulation._FieldState.WHITE else GomokuSimulation._BLACK_COLOR
                    ))

        self.__gui.add_widgets(self.__board_widgets)
