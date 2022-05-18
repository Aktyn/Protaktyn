from typing import Optional, Callable
from src.gui.core.button import Button
from src.gui.core.gui import GUI
from src.gui.core.widget import Widget
from src.gui.views.view_base import ViewBase


class WorkbenchView(ViewBase):
    VIEW_SIZE = 512
    VISUALISATION_SIZE = 256

    def __init__(self, on_start_simulation: Callable[[str], None]):
        self.__gui: Optional[GUI] = None
        self.__on_start_simulation = on_start_simulation

        self.__simulation_buttons = [
            Button(text='Room simulation', pos=(0, 0), font_size=1,
                   on_click=lambda *_: self.__on_start_simulation('room')),
            Button(text='Gomoku simulation', pos=(0, 0), font_size=1,
                   on_click=lambda *_: self.__on_start_simulation('gomoku'))
        ]
        self.__simulation_controls: list[Widget] = []

    def load(self, gui: GUI):
        self.__gui = gui
        gui.set_size((WorkbenchView.VIEW_SIZE, WorkbenchView.VIEW_SIZE + WorkbenchView.VISUALISATION_SIZE))
        width, height = (WorkbenchView.VIEW_SIZE, WorkbenchView.VIEW_SIZE)

        for i, btn in enumerate(self.__simulation_buttons):
            btn.set_pos((width // 2, 40 * (i * 2 + 1)))
        gui.add_widgets(tuple(self.__simulation_buttons))

    def toggle_simulation_buttons(self, enabled: bool):
        if enabled:
            self.__gui.add_widgets(tuple(self.__simulation_buttons))
        else:
            self.__gui.remove_widgets(*self.__simulation_buttons)

    def setup_simulation_controls(self, on_close: Callable, on_toggle_simulation: Callable[[bool], None]):
        # w, h = self.__gui.get_size()

        self.remove_simulation_controls()  # just in case

        close_btn = Button(text='Close', pos=(30, 20), font_size=1, on_click=lambda *_: on_close())
        close_btn.set_size((60, 40))

        simulation_running_button_text = 'Stop simulation'
        simulation_not_running_button_text = 'Start simulation'

        def toggle_simulation(text: str):
            on_toggle_simulation(text == simulation_not_running_button_text)
            toggle_simulation_button.set_text(
                simulation_not_running_button_text if text != simulation_not_running_button_text else simulation_running_button_text)

        toggle_simulation_button = Button(text=simulation_not_running_button_text, pos=(140, 20),
                                          font_size=1,
                                          on_click=lambda *_: toggle_simulation(toggle_simulation_button.get_text()))
        toggle_simulation_button.set_size((140, 40))

        for btn in [close_btn, toggle_simulation_button]:
            btn.set_font_size(0.5)
            btn.set_font_thickness(1)

        self.__simulation_controls = [
            close_btn,
            toggle_simulation_button
        ]
        self.__gui.add_widgets(tuple(self.__simulation_controls), 1)

    def remove_simulation_controls(self):
        for control in self.__simulation_controls:
            self.__gui.remove_widgets(control)
        self.__simulation_controls.clear()
