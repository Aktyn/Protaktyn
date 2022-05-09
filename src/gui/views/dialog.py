from typing import Callable
from src.gui.core.button import Button
from src.gui.core.label import Label
from src.gui.core.gui import GUI
from src.gui.views.view_base import ViewBase


class Dialog(ViewBase):
    def __init__(self, on_confirm: Callable, on_reject: Callable):
        self.__on_confirm = on_confirm
        self.__on_reject = on_reject

    def load(self, gui: GUI):
        width, height = gui.get_size()
        gui.add_widgets((
            Label(text='Are you sure?', pos=(width // 2, height // 2), font_size=2.5),
            Button(text='Confirm', pos=(width // 2 + 160, height // 2 + 120), padding=16, on_click=self.__on_confirm),
            Button(text='Reject', pos=(width // 2 - 160, height // 2 + 120), padding=16, on_click=self.__on_reject)
        ))
