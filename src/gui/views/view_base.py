from abc import abstractmethod


class ViewBase:
    def __int__(self):
        pass

    @abstractmethod
    def load(self, gui: any):
        pass
