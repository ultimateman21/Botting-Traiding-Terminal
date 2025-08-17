from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from pybit.unified_trading import HTTP, WebSocket
from typing import Literal
from math import ceil
from pandas import DataFrame, to_numeric


class Bybit:
    def __init__(self, key: str, secret: str):
        self.key = key
        self.secret = secret

    @staticmethod
    def get_candles(instrument: str, interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M'],
                    from_: int, to_: int, purpose: Literal['single', 'multiple']):
        if isinstance(interval, int):
            str_interval, num_interval = str(interval), interval
        elif interval == 'D':
            str_interval, num_interval = interval, 1440
        elif interval == 'W':
            str_interval, num_interval = interval, 10080
        else:
            str_interval, num_interval = interval, 0

        num_candles = (to_ - from_) // (num_interval * 60 * 1000) if num_interval else 120

        flag = False
        pages = 0
        from__ = from_
        to__ = to_
        if purpose == 'single':
            if num_candles > 720:
                from__ = to_ - 720 * num_interval * 60 * 1000
                flag = True
            pages = 1
        elif purpose == 'multiple':
            pages = ceil(num_candles / 1000) if num_interval > 0 else 1

        session = HTTP()
        all_candles = []
        for page in range(pages):
            if purpose == 'multiple':
                from__ = from_ + (page * num_interval * 60 * 1000 * 1000),
                to__ = from_ + ((page + 1) * num_interval * 60 * 1000 * 1000),
            response = session.get_kline(
                category='spot',
                symbol=instrument,
                interval=str_interval,
                start=from__,
                end=to__,
                limit=1000)
            all_candles[:0] = response['result']['list']
        df = DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])[::-1]

        cols = ['open', 'high', 'low', 'close', 'volume', 'turnover']
        df[cols] = df[cols].apply(to_numeric)

        return [flag, df, num_candles] if flag else [flag, df]

    class CandleStream(QObject):
        newCandle = pyqtSignal(list)
        doStop = pyqtSignal()
        finWork = pyqtSignal()

        def __init__(self, instrument: str, interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M']):
            super().__init__()
            self.symbol = instrument
            self.interval = interval

            self.connection = WebSocket(testnet=False, channel_type='spot')
            self.doStop.connect(self.stop)

        @pyqtSlot()
        def start_work(self):
            if isinstance(self.interval, int):
                self.connection.kline_stream(symbol=self.symbol, interval=self.interval, callback=self.candle_handler)

        def candle_handler(self, message):
            data = message['data'][0]
            if data['confirm']:
                data = [data['start'], data['open'], data['high'], data['low'], data['close'], data['volume'], data['turnover']]
                self.newCandle.emit(data)

        def stop(self):
            self.connection.exit()
            self.finWork.emit()
