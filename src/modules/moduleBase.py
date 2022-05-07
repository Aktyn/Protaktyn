from abc import abstractmethod

from src.commandsInterface import CommandsInterface
from src.gui.core.gui import GUI


class ModuleBase(CommandsInterface):
    def __init__(self, gui: GUI):
        super().__init__(gui)

    @abstractmethod
    def close(self):
        pass
