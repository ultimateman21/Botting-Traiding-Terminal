from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from exchanges.exchange_registry import ExchangeRegistry
from os import makedirs
from os.path import dirname, abspath, join, isdir, isfile
from json import dumps, loads
from pandas import DataFrame


class Logger(QObject):
    appLog = pyqtSignal(str)
    botLog = pyqtSignal(str, str, list)
    requestBotLog = pyqtSignal(str, str, int)
    getBotLog = pyqtSignal(object)
    stopWork = pyqtSignal()
    finWork = pyqtSignal()

    def __init__(self, general_path: str):
        super().__init__()
        self.general_path = general_path
        print(general_path)
        makedirs(self.general_path, exist_ok=True)

        self.logger_thread = QThread()

        self.appLog.connect(self.log_app)
        self.botLog.connect(self.log_bot)
        self.requestBotLog.connect(self.get_log)
        self.stopWork.connect(self.close)

        self.moveToThread(self.logger_thread)
        self.logger_thread.start()

    def log_app(self, log):
        print([log])
        pass

    def log_bot(self, id_, purpose, log):
        print([id_, purpose, log])
        path = join(self.general_path, 'bots', id_)
        makedirs(path, exist_ok=True)

        file_path = path
        line = ''
        if purpose == 'candle':
            file_path = join(path, 'candles.txt')
            line = dumps({'time': log[0], 'candle_delta': log[1], 'delta': log[2],
                          'price': log[3], 'save_price': log[4]}, ensure_ascii=False)
        elif purpose == 'order':
            file_path = join(path, 'orders.txt')
            line = dumps({'time': log[0], 'id': log[1], 'status': log[2], 'lots': log[3],
                          'price': log[4], 'direction': log[5], 'type': log[6]}, ensure_ascii=False)

        with open(file_path, 'a', encoding='cp1251') as f:
            f.write(line + '\n')

    def get_log(self, dir_, file, num):
        path = join(self.general_path, 'bots', dir_, f'{file}.txt')
        if isfile(path):
            with open(path, 'r', encoding='cp1251') as f:
                lines = f.readlines()[-num:]
            logs = [loads(line) for line in lines if line.strip()]
            df = DataFrame(logs)
            self.getBotLog.emit(df)
        else:
            self.getBotLog.emit(DataFrame())

    def close(self):
        self.logger_thread.quit()
        self.logger_thread.wait()
        self.finWork.emit()
