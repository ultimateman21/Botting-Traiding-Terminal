from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable


class AnyMethodThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, method: Callable, params: list):
        super().__init__()
        self.method = method
        self.params = params

    def run(self):
        try:
            res = self.method(*self.params)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(f'{e}')
