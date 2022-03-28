from abc import abstractmethod

from src.commandsInterface import CommandsInterface
from src.gui.gui import GUIEvents


class ModuleBase(CommandsInterface):
    def __init__(self, gui_events: GUIEvents):
        super().__init__()
        self._gui_events = gui_events

    @abstractmethod
    def close(self):
        pass
