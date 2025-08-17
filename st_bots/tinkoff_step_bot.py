from PyQt6.QtCore import QThread, QObject, pyqtSlot, pyqtSignal, QMetaObject, Qt, QEventLoop

from exchanges.exchange_registry import ExchangeRegistry
from treads.any_method_object import AnyMethodObject

from typing import Literal
from decimal import Decimal


class TinkoffStepBot(QObject):
    finWork = pyqtSignal()
    doStop = pyqtSignal()

    def __init__(self, instrument: str, lots: str, interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M'], start_price: Decimal,
                 step: Decimal, slip: Decimal, order_lot: int, start_lot: int, limit: int, sand: bool):
        super().__init__()

        self.instrument = instrument
        self.lots = lots
        self.start_price = start_price
        self.step = step
        self.slip = slip
        self.order_lot = order_lot
        self.start_lot = start_lot
        self.limit = limit
        self.sand = sand

        self.exchange = None
        self.account_id = '3517a708-e31e-42bc-b1bf-a6fdee1ffcf4'

        self.mem_price = None

        self.strategy_thread = QThread()
        self.strategy_thread.start()

        self.strategy_step = None
        self.strategy_step_wait = False

        self.order_state_thread = QThread()
        self.order_state_thread.start()
        self.order_state_result = None

        self.post_order = ExchangeRegistry.pro_get('tinkoff', 'post_order')
        self.is_order_fill = ExchangeRegistry.pro_get('tinkoff', 'is_order_fill')
        self.wait_complete = ExchangeRegistry.pro_get('tinkoff', 'get_order_state_stream')
        self.average_position_price = ExchangeRegistry.pro_get('tinkoff', 'get_average_position_price')
        self.get_position_info = ExchangeRegistry.pro_get('tinkoff', 'get_position_info')
        self.cancel_order = ExchangeRegistry.pro_get('tinkoff', 'cancel_order')

        self.doStop.connect(self.stop)

        self.candle_thread = QThread()
        candle_stream_method = ExchangeRegistry.pro_get('tinkoff', 'get_candle_stream')
        self.candle_stream = candle_stream_method(instrument=self.instrument, interval=interval)
        self.candle_stream.newCandle.connect(self.try_new_candle)
        self.candle_stream.finWork.connect(self.on_stream_fin)
        self.candle_stream.moveToThread(self.candle_thread)

        self.candle_thread.started.connect(self.candle_stream.start_work)

    @pyqtSlot()
    def start_work(self):
        print(1)
        self.start_buy()
        print(2)
        self.candle_thread.start()
        print(3)

    def start_buy(self):
        try:
            self.mem_price = 0

            if self.start_lot == 0:
                self.mem_price = self.start_price
            else:
                if self.start_price == 0:
                    self.post_order(instrument_id=self.instrument,
                                    quantity=self.start_lot,
                                    direction='buy',
                                    order_type='market',
                                    account_id=self.account_id,
                                    sand=self.sand)
                else:
                    order_id_and_status = self.post_order(
                        instrument_id=self.instrument,
                        quantity=self.start_lot,
                        direction='buy',
                        order_type='limit',
                        price=Decimal(str(self.start_price)),
                        account_id=self.account_id,
                        sand=self.sand)
                    if order_id_and_status[0] is not None and not self.is_order_fill(order_id_and_status[1]):
                        def on_order_stream_fin(state):
                            print(state)
                            self.order_state_result = state

                        order_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=0)
                        wait_loop = QEventLoop()
                        order_stream.sendState.connect(on_order_stream_fin)
                        order_stream.sendState.connect(order_stream.deleteLater)
                        order_stream.sendState.connect(wait_loop.quit)
                        order_stream.moveToThread(self.order_state_thread)
                        QMetaObject.invokeMethod(order_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                        wait_loop.exec()
                        if self.order_state_result != 0:
                            self.order_state_result = None

            if self.mem_price == 0:
                self.mem_price = self.average_position_price(self.account_id, self.instrument)
        except Exception as e:
            print('TinkoffStepBot, start_buy ', e)

    def try_new_candle(self, candle: list):
        try:
            if self.strategy_step_wait:
                return

            self.strategy_step_wait = True
            self.strategy_step = AnyMethodObject(self.on_new_candle, [candle])

            self.strategy_step.finished.connect(self.on_new_candle_fin)

            self.strategy_step.moveToThread(self.strategy_thread)
            QMetaObject.invokeMethod(self.strategy_step, 'do_work', Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            print('TinkoffStepBot, try_new_candle ', e)

    def on_new_candle(self, candle):
        try:
            # вычисляем дельту
            print(candle, self.mem_price)
            delta = (candle[4] - self.mem_price) / self.mem_price * 100
            print([delta])
            # logger.warning(f"Candle delta {delta_percent.quantize(Decimal('0.00000'), rounding=ROUND_HALF_DOWN)} - "
            #                f"Delta {percent.quantize(Decimal('0.00000'), rounding=ROUND_HALF_DOWN)} - "
            #                f"Stored price {start_price.quantize(Decimal('0.000'), rounding=ROUND_HALF_DOWN)} - Market price "
            #                f"{quotation_to_decimal(marketdata.candle.close).quantize(Decimal('0.000'), rounding=ROUND_HALF_DOWN)}")
            # сколько инструмента в портфеле и сколько денег в портфеле

            quantity, money = self.get_position_info(self.account_id, self.instrument)
            print([quantity, money])
            if delta > 0:  # продажа
                # если инструмент есть в портфеле
                if quantity is not None:
                    # если хватает количества инструмента на продажу
                    if quantity >= self.lots * self.order_lot:
                        # выставляем заявку
                        if (self.step - self.slip) < abs(delta) < self.step:
                            price = self.mem_price + self.mem_price * (self.step / 100)
                            print(price, 'sell')
                            order_id_and_status = self.post_order(
                                instrument_id=self.instrument,
                                quantity=self.order_lot,
                                direction='sell',
                                order_type='limit',
                                price=Decimal(str(price)),
                                account_id=self.account_id,
                                sand=self.sand)
                        elif abs(delta) > self.step:
                            order_id_and_status = self.post_order(
                                instrument_id=self.instrument,
                                quantity=self.order_lot,
                                direction='sell',
                                order_type='market',
                                # price=Decimal(str(price)),
                                account_id=self.account_id,
                                sand=self.sand)
                        else:
                            order_id_and_status = [None, None]

                        # ждём пока заявка не выполнится
                        print(order_id_and_status, 'sell')
                        if order_id_and_status[0] is not None and not self.is_order_fill(order_id_and_status[1]):
                            def on_order_stream_fin(state):
                                self.order_state_result = state
                            print('wait sell')
                            order_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=3600)
                            wait_loop = QEventLoop()
                            order_stream.sendState.connect(on_order_stream_fin)
                            order_stream.sendState.connect(order_stream.deleteLater)
                            order_stream.sendState.connect(wait_loop.quit)
                            order_stream.moveToThread(self.order_state_thread)
                            QMetaObject.invokeMethod(order_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                            print('wait sell, start')
                            wait_loop.exec()
                            print('wait sell, end')

                            if self.order_state_result != 'expired':
                                self.mem_price = self.order_state_result
                                print(self.mem_price, 'wait sell', self.order_state_result)
                                self.order_state_result = None
                            else:
                                print(self.mem_price, 'wait sell cancel', self.order_state_result)
                                self.cancel_order(self.account_id, order_id_and_status[0])
                                self.order_state_result = None

            elif delta < 0:  # покупка
                buy_flag = False
                if quantity is not None:
                    if quantity < self.limit:  # если число акций меньше лимита
                        buy_flag = True
                else:  # если в портфеле нет выбранного инструмента
                    buy_flag = True

                if buy_flag:
                    # если хватает денег на счету для покупки
                    if money > self.mem_price * self.lots * self.order_lot:
                        # выставляем заявку
                        if (self.step - self.slip) < abs(delta) < self.step:
                            price = self.mem_price - self.mem_price * (self.step / 100)
                            print(price, 'buy')
                            order_id_and_status = self.post_order(
                                instrument_id=self.instrument,
                                quantity=self.order_lot,
                                direction='buy',
                                order_type='limit',
                                price=Decimal(str(price)),
                                account_id=self.account_id,
                                sand=self.sand)
                        elif abs(delta) > self.step:
                            order_id_and_status = self.post_order(
                                instrument_id=self.instrument,
                                quantity=self.order_lot,
                                direction='buy',
                                order_type='market',
                                # price=Decimal(str(price)),
                                account_id=self.account_id,
                                sand=self.sand)
                        else:
                            order_id_and_status = [None, None]
                        print(order_id_and_status, 'buy')
                        # ждём пока заявка не выполнится
                        if order_id_and_status[0] is not None and not self.is_order_fill(order_id_and_status[1]):
                            def on_order_stream_fin(state):
                                self.order_state_result = state

                            print('wait buy')
                            order_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=3600)
                            wait_loop = QEventLoop()
                            order_stream.sendState.connect(on_order_stream_fin)
                            order_stream.sendState.connect(order_stream.deleteLater)
                            order_stream.sendState.connect(wait_loop.quit)
                            order_stream.moveToThread(self.order_state_thread)
                            QMetaObject.invokeMethod(order_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                            print('wait buy, start')
                            wait_loop.exec()
                            print('wait buy, end')

                            if self.order_state_result != 'expired':
                                print(self.mem_price, self.start_price, 'wait buy', self.order_state_result)
                                if self.order_state_result > self.start_price:
                                    self.mem_price = self.order_state_result
                                else:
                                    self.mem_price = self.start_price
                                self.order_state_result = None
                            else:
                                print(self.mem_price, 'wait sell cancel', self.order_state_result)
                                self.cancel_order(self.account_id, order_id_and_status[0])
                                self.order_state_result = None
        except Exception as e:
            print('TinkoffStepBot, on_new_candle ', e)

    def on_new_candle_fin(self, res: None):
        self.strategy_step.deleteLater()
        self.strategy_step = None
        self.strategy_step_wait = False

    def on_stream_fin(self):
        self.candle_stream.deleteLater()
        self.candle_thread.quit()
        self.candle_thread.wait()
        self.finWork.emit()

    def stop(self):
        self.candle_stream.doStop.emit()
