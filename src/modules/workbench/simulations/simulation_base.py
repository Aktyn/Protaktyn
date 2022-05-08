import time
import pymunk
from abc import abstractmethod
from threading import Thread
from pymunk import Vec2d
from src.gui.core.gui import GUI
from src.gui.core.image import Image
from src.modules.workbench.view import WorkbenchView


class SimulationBase:
    class _Box:
        def __init__(self, pos=(0.0, 0.0), size=(0.1, 0.1), dynamic=True):
            self.pos = pos
            self.size = size

            self.body = pymunk.Body(1, 0.5, pymunk.Body.DYNAMIC if dynamic else pymunk.Body.STATIC)
            self.body.position = Vec2d(*self.pos)

            self.poly = pymunk.Poly.create_box(self.body, self.size)
            self.poly.mass = 1  # 10
            self.poly.elasticity = 0.99
            self.poly.friction = 0.99

            self.img = Image(
                pos=(0, 0),
                size=(int(self.size[0] * WorkbenchView.VIEW_SIZE), int(self.size[1] * WorkbenchView.VIEW_SIZE)),
                fill=(255, 255, 255)
            )
            self.update()

        def update(self):
            self.img.set_pos((
                int((self.body.position.x + 0.5 - self.size[0] / 2) * WorkbenchView.VIEW_SIZE),
                int((0.5 - self.body.position.y - self.size[1] / 2) * WorkbenchView.VIEW_SIZE)
            ))
            # TODO: try this only on dynamic objects
            self.img.set_angle(self.body.angle)

    def __init__(self, gui: GUI, gravity=(0.0, 0.0)):
        self._gui = gui
        self._is_running = False

        self.__objects: list[SimulationBase._Box] = []

        self.__space = pymunk.Space()
        self.__space.gravity = gravity

        self._simulation_process = Thread(target=self.__simulation_thread, daemon=True)
        self._simulation_process.start()

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def _init(self):
        pass

    @abstractmethod
    def _update(self, delta_time: float):
        pass

    def _add_objects(self, *objects: _Box):
        for obj in objects:
            self.__objects.append(obj)
            self.__space.add(obj.body, obj.poly)
            self._gui.add_widgets(obj.img)

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

            self._update(delta_time)  # TODO: delta time
            self.__space.step(delta_time)
            for obj in self.__objects:
                obj.update()
            self._gui.redraw()
            time.sleep(max(0.0, 1.0 / 60.0 - (time.time() - now)))
