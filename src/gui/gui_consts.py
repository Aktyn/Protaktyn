from src.utils import no_full_screen


class GUIConsts:
    BACKGROUND_COLOR = "#546E7A"
    TEXT_COLOR = "#ECEFF1"
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 480
    BUTTON_WIDTH = 100
    TOP_BAR_HEIGHT = 30
    FULL_SCREEN = not no_full_screen()
