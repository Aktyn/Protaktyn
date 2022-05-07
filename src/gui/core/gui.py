from src.common.utils import show_gui
from typing import Callable, Optional
from src.gui.core.button import Button
from src.gui.core.widget import Widget
from src.gui.views.view_base import ViewBase

if show_gui():
    import sys
    import numpy as np
    import cv2
    from cv2 import VideoCapture

    from threading import Thread
    from src.gui.core.gui_consts import GUIConsts


    class GUI:
        __COUNTER = 0
        _DEFAULT_WIDTH = 640
        _DEFAULT_HEIGHT = 360

        def __init__(self, on_close: Callable, size: tuple[int, int] = (_DEFAULT_WIDTH, _DEFAULT_HEIGHT)):
            self.__running = False
            self.__need_redraw = False
            self.__title = GUIConsts.WINDOW_TITLE
            self.__on_close = on_close
            self.__size = size
            self.__current_view: Optional[ViewBase] = None

            self.__camera_frames_history: list[any] = []
            self.__camera_frames_history_buffer_size = 60

            self.__background_color = (56, 50, 38)

            self.__widgets: list[Widget] = []
            self.__camera_stream: Optional[VideoCapture] = None

            self.__window_thread = Thread(target=self.__init_window, daemon=True)
            self.__window_thread.start()

        def close(self):
            self.__running = False

            self.stop_camera_preview()

            # noinspection PyBroadException
            try:
                cv2.destroyWindow(self.__title)
            except BaseException:
                pass
            if self.__window_thread is not None:
                # noinspection PyBroadException
                try:
                    self.__window_thread.join()
                except BaseException:
                    pass
                self.__window_thread = None

        def get_size(self):
            return self.__size

        def set_title(self, title: str):
            # noinspection PyBroadException
            try:
                cv2.setWindowTitle(self.__title, title)
            except BaseException:
                pass

        def start_camera_preview(self, resolution: tuple[int, int], camera_id=0):
            if self.__camera_stream is not None:
                print("Camera preview already started")
                return
            self.__camera_stream = cv2.VideoCapture(camera_id)
            self.__camera_stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.__camera_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        def stop_camera_preview(self):
            if self.__camera_stream is not None:
                self.__camera_stream.release()
                self.__camera_stream = None
            self.__camera_frames_history.clear()

        def get_last_camera_frame(self):
            if len(self.__camera_frames_history) > 0:
                return self.__camera_frames_history[-1]
            return None

        def __init_window(self):
            self.__running = True
            self.__need_redraw = True
            width, height = self.__size

            cv2.namedWindow(self.__title, cv2.WINDOW_AUTOSIZE | cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.__title, width, height)
            # cv2.moveWindow(self.__title, 0, 0)
            cv2.setMouseCallback(self.__title, self.__handle_mouse_event)

            img = np.full(shape=(height, width, 3), fill_value=self.__background_color, dtype=np.uint8)

            while self.__running:
                if cv2.getWindowProperty(self.__title, cv2.WND_PROP_VISIBLE) < 1:
                    if self.__on_close is not None:
                        self.__on_close()
                        break
                    else:
                        sys.exit(0)

                if self.__camera_stream is not None and self.__camera_stream.isOpened():
                    success, camera_image = self.__camera_stream.read()
                    if success:
                        self.__camera_frames_history.append(camera_image)
                        while len(self.__camera_frames_history) > self.__camera_frames_history_buffer_size:
                            self.__camera_frames_history.pop(0)
                        for widget in self.__widgets:
                            widget.draw(camera_image)
                        # noinspection PyBroadException
                        try:
                            if self.__running:
                                cv2.imshow(self.__title, camera_image)
                        except BaseException:
                            pass
                    # else:
                    #     print("ERROR: Unable to read from webcam. Please verify your webcam settings.")
                    #     self.stop_camera_preview()
                else:
                    if self.__need_redraw:
                        img = np.full(shape=(height, width, 3), fill_value=self.__background_color, dtype=np.uint8)
                        for widget in self.__widgets:
                            widget.draw(img)
                        self.__need_redraw = False

                    # noinspection PyBroadException
                    try:
                        if self.__running:
                            cv2.imshow(self.__title, img)
                    except BaseException:
                        pass
                cv2.waitKey(1) & 0xFF
            del img

        def redraw(self):
            self.__need_redraw = True

        def __handle_mouse_event(self, event: int, x: int, y: int, _flags: any, _param: any):
            for widget in self.__widgets:
                if type(widget) == Button:
                    # noinspection PyTypeChecker
                    button = widget  # type: Button
                    if button.is_disabled():
                        continue
                    is_cursor_over = button.is_point_inside(x, y)
                    if event == cv2.EVENT_MOUSEMOVE:
                        if button.toggle_hover(is_cursor_over):
                            self.__need_redraw = True
                    elif event == cv2.EVENT_LBUTTONDOWN and is_cursor_over:
                        button.on_mouse_down()
                    elif event == cv2.EVENT_LBUTTONUP and is_cursor_over:
                        button.on_mouse_up()
                        button.click()

        def get_view(self):
            return self.__current_view

        def set_view(self, view: ViewBase):
            self.remove_all_widgets()
            self.__current_view = view
            view.load(self)
            self.__need_redraw = True

        def clear_view(self):
            self.__current_view = None
            self.remove_all_widgets()

        def add_widgets(self, *widgets: Widget):
            self.__widgets.extend(widgets)
            self.__need_redraw = True

        def remove_widgets(self, *widgets: Widget):
            for widget in widgets:
                if self.__widgets.count(widget) > 0:
                    self.__widgets.remove(widget)
            self.__need_redraw = True

        def remove_all_widgets(self):
            self.__widgets.clear()
            self.__need_redraw = True

else:
    # Mock GUI TODO: camera preview functionality
    class GUI:
        _DEFAULT_WIDTH = 640
        _DEFAULT_HEIGHT = 480

        def __init__(self, _on_close: Callable, _size: tuple[int, int] = (_DEFAULT_WIDTH, _DEFAULT_HEIGHT)):
            pass

        def close(self):
            pass

        def start_camera_preview(self, resolution: tuple[int, int], camera_id=0):
            pass

        def stop_camera_preview(self):
            pass

        def get_last_camera_frame(self):
            pass

        def get_size(self):
            pass

        def set_title(self, title: str):
            pass

        def redraw(self):
            pass

        def get_view(self):
            pass

        def set_view(self, view: ViewBase):
            pass

        def clear_view(self):
            pass

        def add_widget(self, widget: Widget):
            pass

        def remove_widgets(self, widget: Widget):
            pass

        def remove_all_widgets(self):
            pass
