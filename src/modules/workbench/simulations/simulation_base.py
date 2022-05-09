import time
from typing import Optional

import pymunk
from abc import abstractmethod
from threading import Thread
from pymunk import Vec2d
from src.gui.core.gui import GUI
from src.gui.core.line import Line
from src.gui.core.rect import Rect
from src.gui.core.widget import Widget
from src.modules.workbench.view import WorkbenchView


class SimulationBase:
    class _Object:
        def __init__(self, pos=(0.0, 0.0), color=(255, 255, 255)):
            self.pos = pos
            self._color = color
            self.body: Optional[pymunk.Body] = None
            self.shape: Optional[pymunk.Shape] = None
            self.widget: Optional[Widget] = None

        def set_color(self, color):
            self._color = color

        @abstractmethod
        def update(self, camera_pos: tuple[float, float]):
            pass

    class _BodyEx(pymunk.Body):
        def __init__(self, mass: float = 0, moment: float = 0, body_type: int = pymunk.Body.DYNAMIC):
            super().__init__(mass, moment, body_type)

        def set_velocity(self, velocity: tuple[float, float]):
            # noinspection PyArgumentList
            super()._set_velocity(vel=velocity)

        def set_angular_velocity(self, angular_velocity: float):
            # noinspection PyArgumentList
            super()._set_angular_velocity(angular_velocity)

        def set_collision_filtering(self, categories: int, mask: int):
            __filter = pymunk.ShapeFilter(categories=categories, mask=mask)
            for __shape in self.shapes:
                __shape.filter = __filter

    class _Line(_Object):
        def __init__(self, pos_start=(0., 0.), pos_end=(0., 0.), color=(255, 255, 255)):
            super().__init__(pos_start, color)
            self.pos_end = pos_end

            self.widget = Line(color=self._color)

        def set_color(self, color: tuple[int, int, int]):
            super().set_color(color)
            self.widget.set_color(color)

        def update(self, camera_pos: tuple[float, float]):
            self.widget.set_points((
                int((self.pos[0] + 0.5 - camera_pos[0]) * WorkbenchView.VIEW_SIZE),
                int((0.5 - self.pos[1] + camera_pos[1]) * WorkbenchView.VIEW_SIZE)
            ), (
                int((self.pos_end[0] + 0.5 - camera_pos[0]) * WorkbenchView.VIEW_SIZE),
                int((0.5 - self.pos_end[1] + camera_pos[1]) * WorkbenchView.VIEW_SIZE)
            ))

    class _Box(_Object):
        def __init__(self, pos=(0.0, 0.0), size=(0.1, 0.1), color=(255, 255, 255), dynamic=True, sensor=False):
            super().__init__(pos, color)
            self.size = size

            self.body = SimulationBase._BodyEx(1, 0.5, pymunk.Body.DYNAMIC if dynamic else pymunk.Body.STATIC)
            self.body.position = Vec2d(*self.pos)

            self.shape = pymunk.Poly.create_box(self.body, self.size)
            self.shape.mass = 1  # 10
            self.shape.elasticity = 0.99
            self.shape.friction = 0.99
            self.shape.sensor = sensor

            self.widget = Rect(
                pos=(0, 0),
                size=(int(self.size[0] * WorkbenchView.VIEW_SIZE), int(self.size[1] * WorkbenchView.VIEW_SIZE)),
                background_color=self._color
            )
            self.update((0, 0))

        def update(self, camera_pos: tuple[float, float]):
            self.pos = (self.body.position.x, self.body.position.y)
            self.widget.set_pos((
                int((self.body.position.x + 0.5 - camera_pos[0]) * WorkbenchView.VIEW_SIZE),
                int((0.5 - self.body.position.y + camera_pos[1]) * WorkbenchView.VIEW_SIZE)
            ))
            self.widget.set_angle(self.body.angle)

    def __init__(self, gui: GUI, gravity=(0.0, 0.0), damping=0.99):
        self._gui = gui
        self.__is_running = False

        self.__camera_pos = (0.0, 0.0)
        self.__objects: list[SimulationBase._Object] = []
        self.__empty_filter = pymunk.ShapeFilter()

        self.__space = pymunk.Space()
        self.__space.gravity = gravity
        self.__space.damping = damping
        self.__space.collision_bias = 0.01
        self.__space.collision_slop = 0.01
        self.__space.collision_persistence = 8

        self._simulation_process: Optional[Thread] = None

    @abstractmethod
    def close(self):
        self.__is_running = False
        if self._simulation_process is not None:
            self._simulation_process.join()

    def _start(self):
        self._simulation_process = Thread(target=self.__simulation_thread, daemon=True)
        self._simulation_process.start()

    @abstractmethod
    def _init(self):
        pass

    @abstractmethod
    def _update(self, delta_time: float):
        pass

    def _add_objects(self, *objects: _Object):
        for obj in objects:
            self.__objects.append(obj)
            if obj.body:
                self.__space.add(obj.body)
            if obj.shape:
                self.__space.add(obj.shape)
            if obj.widget is not None:
                self._gui.add_widgets(obj.widget)

    def _ray_cast(self, from_point: tuple[float, float], to_point: tuple[float, float], mask=0xFFFFFFFF):
        segment_q = self.__space.segment_query_first(start=from_point, end=to_point, radius=0.00001,
                                                     shape_filter=pymunk.ShapeFilter(
                                                         mask=mask) if mask != 0xFFFFFFFF else self.__empty_filter)
        if segment_q:
            return segment_q.point.x, segment_q.point.y
        return None

    def _set_camera_pos(self, pos: tuple[float, float]):
        self.__camera_pos = pos

    def __simulation_thread(self):
        self.__is_running = True

        self._init()

        counter = 0
        last = time.time()

        while self.__is_running:
            now = time.time()
            delta_time = now - last
            if int(now) > int(last):
                print(f"FPS: {counter}")
                counter = 0
            counter += 1
            last = now

            self._update(delta_time)
            self.__space.step(delta_time)
            for obj in self.__objects:
                obj.update(self.__camera_pos)
            self._gui.redraw()
            time.sleep(max(0.0, 1.0 / 60.0 - (time.time() - now)))
