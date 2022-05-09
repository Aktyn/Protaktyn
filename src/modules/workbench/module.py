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
        self.__stop_simulation()
        super().close()

    def __stop_simulation(self):
        self.__view.toggle_simulation_buttons(True)

        if self.__simulation is None:
            return
        self.__simulation.close()
        self.__simulation = None
        self.__view.remove_simulation_controls()

    def __start_simulation(self, simulation_name: str):
        self.__view.toggle_simulation_buttons(False)

        if simulation_name == 'room':
            self.__simulation = RoomSimulation(self._gui)
            self.__view.setup_simulation_controls(on_close=self.__stop_simulation,
                                                  on_toggle_simulation=self.__simulation.toggle_simulate)
