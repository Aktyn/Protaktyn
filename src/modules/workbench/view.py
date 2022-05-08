from typing import Optional, Callable
from src.gui.core.button import Button
from src.gui.core.gui import GUI
from src.gui.views.view_base import ViewBase


class WorkbenchView(ViewBase):
    VIEW_SIZE = 512

    def __init__(self, on_start_simulation: Callable[[str], None]):
        self.__gui: Optional[GUI] = None
        self.__on_start_simulation = on_start_simulation

        self.__simulation_buttons = [
            Button(text='Room simulation', pos=(0, 0), font_size=1,
                   on_click=lambda: self.__on_start_simulation('room'))
        ]

    def load(self, gui: GUI):
        self.__gui = gui
        gui.set_size((WorkbenchView.VIEW_SIZE, WorkbenchView.VIEW_SIZE))
        width, height = (WorkbenchView.VIEW_SIZE, WorkbenchView.VIEW_SIZE)

        for i, btn in enumerate(self.__simulation_buttons):
            btn.set_pos((width // 2, 40 * (i + 1)))
        gui.add_widgets(*self.__simulation_buttons)

    def toggle_simulation_buttons(self, enabled: bool):
        if enabled:
            self.__gui.add_widgets(*self.__simulation_buttons)
        else:
            self.__gui.remove_widgets(*self.__simulation_buttons)

