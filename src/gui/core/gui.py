from src.common.common_utils import show_gui
from typing import Callable, Optional, Union
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
        DEFAULT_SIZE = (640, 360)

        def __init__(self, on_close: Callable, size: tuple[int, int] = DEFAULT_SIZE):
            self.__running = False
            self.__need_redraw = False
            self.__title = GUIConsts.WINDOW_TITLE
            self.__on_close = on_close
            self.__size = size
            self.__current_view: Optional[ViewBase] = None
            self.key = 255

            self.__camera_frames_history: list[any] = []
            self.__camera_frames_history_buffer_size = 60

            self.__background_color = (56, 50, 38)
            self.__img = np.full(shape=(size[1], size[0], 3), fill_value=self.__background_color,
                                 dtype=np.uint8)

            self.__widgets: list[list[Widget]] = []
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

            del self.__img

        def get_size(self):
            return self.__size

        def set_size(self, size: tuple[int, int]):
            self.__size = size
            # noinspection PyBroadException
            # try:
            #     cv2.resizeWindow(self.__title, size[0], size[1])
            # except BaseException:
            #     pass

        def set_title(self, title: str):
            # noinspection PyBroadException
            try:
                cv2.setWindowTitle(self.__title, title)
            except BaseException:
                pass

        def start_camera_preview(self, resolution: tuple[int, int] = DEFAULT_SIZE, camera_id=0):
            if self.__camera_stream is not None:
                print("Camera preview already started")
                return
            print("Starting camera preview. Camera id:", camera_id)

            try:
                self.__camera_stream = cv2.VideoCapture(camera_id)
                self.__camera_stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
                self.__camera_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            except BaseException as e:
                print("Failed to start camera preview:", e)

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

            def __draw_frame(camera_frame: Optional[np.ndarray] = None):
                if self.__need_redraw or camera_frame is not None:

                    self.__img = np.full(shape=(self.__size[1], self.__size[0], 3), fill_value=self.__background_color,
                                         dtype=np.uint8)

                    if camera_frame is not None:
                        h2, w2 = camera_frame.shape[:2]
                        self.__img[:h2, :w2] = camera_frame

                    for __widgets_layer in self.__widgets:
                        for __widget in __widgets_layer:
                            __widget.draw(self.__img)
                    self.__need_redraw = False

                # noinspection PyBroadException
                try:
                    if self.__running:
                        cv2.imshow(self.__title, self.__img)
                except BaseException:
                    pass

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
                        height, width = camera_image.shape[:2]
                        self.__camera_frames_history.append(camera_image)

                        while len(self.__camera_frames_history) > self.__camera_frames_history_buffer_size:
                            self.__camera_frames_history.pop(0)

                        if width == self.__size[0] and height == self.__size[1]:
                            for widgets_layer in self.__widgets:
                                for widget in widgets_layer:
                                    widget.draw(camera_image)
                            # noinspection PyBroadException
                            try:
                                if self.__running:
                                    cv2.imshow(self.__title, camera_image)
                            except BaseException:
                                pass
                        else:
                            __draw_frame(camera_image)
                else:
                    __draw_frame()
                self.key = cv2.waitKey(1) & 0xFF

        def redraw(self):
            self.__need_redraw = True

        def __handle_mouse_event(self, event: int, x: int, y: int, _flags: any, _param: any):
            for widgets_layer in self.__widgets:
                for widget in widgets_layer:
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

        def add_widgets(self, widgets: Union[tuple[Widget, ...], list[Widget]], z_index: int = 0):
            while len(self.__widgets) <= z_index:
                self.__widgets.append([])
            self.__widgets[z_index].extend(widgets)
            self.__need_redraw = True

        def remove_widgets(self, *widgets: Widget):
            # for widgets_layer in widgets:
            for widget in widgets:
                for widgets_layer in self.__widgets:
                    if widgets_layer.count(widget) > 0:
                        widgets_layer.remove(widget)
                        break
            self.__need_redraw = True

        def remove_all_widgets(self):
            for layer in self.__widgets:
                layer.clear()
            self.__widgets.clear()
            self.__need_redraw = True

else:
    # Mock GUI TODO: camera preview functionality
    class GUI:
        DEFAULT_SIZE = (640, 360)

        def __init__(self, _on_close: Callable, _size: tuple[int, int] = DEFAULT_SIZE):
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

        def set_size(self, size: tuple[int, int]):
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

        def add_widgets(self, widgets: Union[tuple[Widget, ...], list[Widget]], z_index: int = 0):
            pass

        def remove_widgets(self, *widgets: Widget):
            pass

        def remove_all_widgets(self):
            pass
