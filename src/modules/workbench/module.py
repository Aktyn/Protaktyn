from typing import Optional

from src.gui.core.gui import GUI
from src.modules.moduleBase import ModuleBase
from src.modules.workbench.simulations.room import RoomSimulation
from src.modules.workbench.simulations.simulation_base import SimulationBase

from src.modules.workbench.view import WorkbenchView


# This module can only be opened via command argument: start-module="workbench"
class WorkbenchModule(ModuleBase):
    def __init__(self, gui: GUI):
        super().__init__(gui)

        self.__view = WorkbenchView(on_start_simulation=self.__start_simulation)
        self._gui.set_view(self.__view)

        self.__simulation: Optional[SimulationBase] = None

    def close(self):
        if self.__simulation is not None:
            self.__simulation.close()
            self.__simulation = None
        super().close()

    def __start_simulation(self, simulation_name: str):
        self.__view.toggle_simulation_buttons(False)

        if simulation_name == 'room':
            self.__simulation = RoomSimulation(self._gui)
