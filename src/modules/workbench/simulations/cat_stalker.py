from src.gui.core.gui import GUI
from src.modules.workbench.simulations.physics_simulation_base import PhysicsSimulationBase


class CatStalkerSimulation(PhysicsSimulationBase):
    def __init__(self, gui: GUI):
        super().__init__(gui, gravity=(0, 0), damping=0.02)

    def close(self):
        super().close()

    def _on_init(self):
        pass

    def _on_update(self, delta_time: float):
        pass
