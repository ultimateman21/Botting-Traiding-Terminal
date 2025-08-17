from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Callable


class AnyMethodObject(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, method: Callable, params: list):
        super().__init__()
        self.method = method
        self.params = params

    @pyqtSlot()
    def do_work(self):
        try:
            res = self.method(*self.params)
            self.finished.emit(res)
        except Exception as e:
            print(f'AnyMethodObject, {self.method} ', e)
            self.error.emit(f'{e}')
