from PyQt6.QtCore import QThread, pyqtSignal
from pybit.unified_trading import WebSocket
from time import sleep


class CandleStreamThread(QThread):
    new_candle = pyqtSignal(list)

    def __init__(self, symbol, interval):
        super().__init__()
        self.symbol = symbol
        self.interval = interval
        self.running = True

    def run(self):
        def candle_handler(message):
            data = message['data'][0]
            if self.running and data['confirm']:
                sent_message = [data['start'], data['open'], data['high'], data['low'], data['close'], data['volume'], data['turnover']]
                self.new_candle.emit(sent_message)

        ws = WebSocket(testnet=False, channel_type='spot')
        ws.kline_stream(interval=self.interval, symbol=self.symbol, callback=candle_handler)

        while self.running:
            sleep(1)

        ws.exit()

    def stop(self):
        self.running = False
        self.wait()
