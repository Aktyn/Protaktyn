import random

from src.gui.core.gui import GUI
from src.modules.workbench.simulations.simulation_base import SimulationBase


class RoomSimulation(SimulationBase):
    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, -0.05))

    def close(self):
        super().close()

    def _init(self):
        self._add_objects(
            *map(lambda i: SimulationBase._Box(pos=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4))), range(10))
        )

        for y in range(11):
            for x in range(11):
                if x == 0 or x == 10 or y == 0 or y == 10:
                    self._add_objects(
                        SimulationBase._Box(pos=(-0.5 + x * 0.1, -0.5 + y * 0.1), size=(0.1, 0.1), dynamic=False))

    def _update(self, delta_time: float):
        pass
