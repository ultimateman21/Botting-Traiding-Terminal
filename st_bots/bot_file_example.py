from PyQt6.QtCore import pyqtSignal, QObject, QThread, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton

from exchanges.exchange_registry import ExchangeRegistry


class BotSets(QWidget):
    statusGet = pyqtSignal(str, int)
    startBot = pyqtSignal(list)
    stopBot = pyqtSignal(str)
    deleteBot = pyqtSignal(str)

    def __init__(self, exchange: str, instrument: str, rep_id: str):
        super().__init__()
        self.exchange = exchange
        self.instrument = instrument
        self.rep_id = rep_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox('Параметры')
        set_layout = QHBoxLayout(box)
        set_layout.setContentsMargins(7, 2, 7, 7)

        # ...

        self.start_b = QPushButton('Запустить')
        self.start_b.clicked.connect(self.start)
        set_layout.addWidget(self.start_b)

        self.stop_b = QPushButton('Остановить')
        self.stop_b.clicked.connect(self.stop)
        set_layout.addWidget(self.stop_b)

        self.del_b = QPushButton('Удалить')
        self.del_b.clicked.connect(self.delete)
        set_layout.addWidget(self.del_b)

        # ...

        layout.addWidget(box)

    def start(self):
        self.stop_b.setEnabled(True)
        self.start_b.setEnabled(False)
        self.del_b.setEnabled(False)

        data = None  # некоторый набор параметров

        self.startBot.emit(data)

    def stop(self):
        self.start_b.setEnabled(True)
        self.stop_b.setEnabled(False)
        self.del_b.setEnabled(True)
        self.stopBot.emit(self.rep_id)

    def delete(self):
        self.deleteBot.emit(self.rep_id)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)


class SomeStrategyBot(QObject):
    finWork = pyqtSignal()
    doStop = pyqtSignal()

    def __init__(self, exchange: str, instrument: str,
                 # остальные параметры
                 interval
                 ):
        super().__init__()
        self.exchange = exchange
        self.instrument = instrument
        # параметры
        # ...

        # доступ к бирже
        self.some_method_or_class = ExchangeRegistry.pro_get(self.exchange, 'method_or_class_name')
        # ...

        # вызов завершения стрима свеч
        self.doStop.connect(self.stop)

        # подключение стрима свеч
        self.candle_thread = QThread()
        candle_stream_method = ExchangeRegistry.pro_get(self.exchange, 'get_candle_stream')
        self.candle_stream = candle_stream_method(instrument=self.instrument, interval=interval)
        self.candle_stream.newCandle.connect(self.try_new_candle)
        self.candle_stream.finWork.connect(self.on_stream_fin)
        self.candle_stream.moveToThread(self.candle_thread)

        self.candle_thread.started.connect(self.candle_stream.start_work)

    @pyqtSlot()
    def start_work(self):
        self.candle_thread.start()

    def try_new_candle(self, candle: list):
        pass
        # шаг стратегии
        # ...

    def on_stream_fin(self):
        self.candle_stream.deleteLater()
        self.candle_thread.quit()
        self.candle_thread.wait()
        self.finWork.emit()

    def stop(self):
        self.candle_stream.doStop.emit()
