from datetime import datetime

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGroupBox, QHBoxLayout, QGridLayout, QFormLayout, QLabel, QComboBox, QCheckBox, QFrame, \
    QSpinBox, QMessageBox, QSizePolicy
from PyQt6.QtCore import QThread, QObject, pyqtSlot, pyqtSignal, QMetaObject, Qt, QEventLoop, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor

from os.path import dirname, abspath, join

from elements.VariableDischargesSpinBox import VariableDischargesSpinBox

from treads.any_method_tread import AnyMethodThread

from exchanges.exchange_registry import ExchangeRegistry
from treads.any_method_object import AnyMethodObject

from typing import Literal
from decimal import Decimal


class BotSets(QWidget):
    statusGet = pyqtSignal(str, int)
    startBot = pyqtSignal(dict)
    stopBot = pyqtSignal(str)
    deleteBot = pyqtSignal(str)

    def __init__(self, exchange: str, instrument: dict, rep_id: str):
        super().__init__()
        self.exchange = exchange
        self.instrument = instrument
        self.rep_id = rep_id

        self.thread = None
        self.o_tread = QThread()
        self.o_tread.start()
        self.is_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 0, 3, 1)

        box = QGroupBox('Параметры')
        box.setStyleSheet('QGroupBox {background-color: #f0f0f0; margin-top: 8px;}'
                          'QGroupBox::title {subcontrol-origin: padding; subcontrol-position: top left; margin: -18px 0 0 7px;'
                          'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffffff, stop: 0.499 #ffffff,'
                          'stop: 0.501 #f0f0f0, stop: 1 #f0f0f0);}')
        set_layout = QHBoxLayout(box)
        set_layout.setContentsMargins(7, 9, 7, 7)

        set_l_layout = QGridLayout()
        set_l_layout.setVerticalSpacing(2)

        account_layout = QFormLayout()
        account_layout.setHorizontalSpacing(7)
        self.account_combo = QComboBox()
        account_layout.addRow('Счёт:', self.account_combo, )
        set_l_layout.addLayout(account_layout, 0, 0)

        instrument_label = QLabel(self.instrument['ticker'])
        instrument_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        set_l_layout.addWidget(instrument_label, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)

        price_layout = QFormLayout()
        price_layout.setHorizontalSpacing(7)
        self.price_label = QLabel()
        self.price_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        price_layout.addRow('Стоимость:', self.price_label)
        set_l_layout.addLayout(price_layout, 0, 2)

        lot_layout = QFormLayout()
        lot_layout.setHorizontalSpacing(7)
        self.lot_label = QLabel()
        self.lot_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # self.lot_label.setContentsMargins(0, 0, 3, 0)
        # self.lot_label.setStyleSheet('background-color: white')
        # self.lot_label.setMinimumWidth(10)
        lot_layout.addRow('Лотность:', self.lot_label)
        set_l_layout.addLayout(lot_layout, 0, 3)

        self.r_button = QPushButton()
        self.r_button.setFixedSize(30, 24)
        self.r_button.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/reset.png')))
        self.r_button.clicked.connect(self.get_accounts)
        self.r_button.clicked.connect(self.get_accounts)
        set_l_layout.addWidget(self.r_button, 0, 4)

        self.timeframe = QComboBox()
        self.timeframe.setMinimumWidth(85)
        self.timeframe.setMaxVisibleItems(4)
        frames = [('1 минута', 1), ('3 минуты', 3), ('5 минут', 5), ('15 минут', 15), ('Пол часа', 30),
                  ('1 час', 60), ('2 часа', 120), ('4 часа', 240), ('Сутки', 'D'), ('Неделя', 'W'),
                  ('Месяц', 'M')]
        [self.timeframe.addItem(*cor) for cor in frames]
        # self.timeframe.currentTextChanged.connect(self.check_options)
        set_l_layout.addWidget(self.timeframe, 1, 0)

        start_price_layout = QFormLayout()
        start_price_layout.setHorizontalSpacing(7)
        self.price = VariableDischargesSpinBox('руб')
        self.price.setFixedHeight(22)
        # self.price.setMinimumWidth(150)
        start_price_layout.addRow('Стартовая цена:', self.price)
        set_l_layout.addLayout(start_price_layout, 1, 1, 1, 3)

        self.sand_check = QCheckBox()
        self.sand_check.setFixedWidth(20)
        self.sand_check.setStyleSheet('QCheckBox::indicator {{background-color: white; width: 18px; height: 18px; border: 1px solid black;}}'
                                      'QCheckBox::indicator:checked {{image: url({});}} QCheckBox::indicator:checked:hover {{image: url({});}}'
                                      'QCheckBox::indicator:disabled {{border: 1px solid #cccccc;}}'
                                      'QCheckBox::indicator:hover {{border: 1px solid #0078d7;}}'.format(
                                       join(dirname(abspath(__file__)), '../source/check.png').replace('\\', '/'),
                                       join(dirname(abspath(__file__)), '../source/check_hover.png').replace('\\', '/')))
        self.sand_check.setToolTip('Песочница')
        set_l_layout.addWidget(self.sand_check, 1, 4, alignment=Qt.AlignmentFlag.AlignCenter)

        set_layout.addLayout(set_l_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        palette = line.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        line.setPalette(palette)
        set_layout.addWidget(line)

        set_r_layout = QVBoxLayout()
        set_r_layout.setSpacing(3)

        up_set_r_layout = QHBoxLayout()
        up_set_r_layout.setSpacing(7)

        step_layout = QFormLayout()
        self.step_perc = VariableDischargesSpinBox('%')
        self.step_perc.setFixedHeight(22)
        step_layout.addRow('Шаг:', self.step_perc)
        up_set_r_layout.addLayout(step_layout)

        slip_layout = QFormLayout()
        self.slip_perc = VariableDischargesSpinBox('%')
        self.slip_perc.setFixedHeight(22)
        slip_layout.addRow('Проскальзывание:', self.slip_perc)
        up_set_r_layout.addLayout(slip_layout)

        order_lot_layout = QFormLayout()
        self.order_lot = QSpinBox()
        self.order_lot.setFixedHeight(22)
        self.order_lot.setRange(1, 10000)
        order_lot_layout.addRow('Лотов на ордер:', self.order_lot)
        up_set_r_layout.addLayout(order_lot_layout)

        set_r_layout.addLayout(up_set_r_layout)

        down_set_r_layout = QHBoxLayout()
        down_set_r_layout.setSpacing(7)

        start_buy_layout = QFormLayout()
        self.start_buy = QSpinBox()
        self.start_buy.setFixedHeight(22)
        self.start_buy.setSuffix(' лотов')
        self.start_buy.setRange(0, 10000)
        self.start_buy.setSpecialValueText('не покупать')
        start_buy_layout.addRow('Купить при пуске:', self.start_buy)
        down_set_r_layout.addLayout(start_buy_layout)

        limit_layout = QFormLayout()
        self.limit = QSpinBox()
        self.limit.setFixedHeight(22)
        self.limit.setRange(1, 10000)
        self.limit.setSuffix(' акций')
        limit_layout.addRow('Лимит счёта:', self.limit)
        down_set_r_layout.addLayout(limit_layout)

        self.start_b = QPushButton('Запустить')
        self.start_b.setEnabled(False)
        self.start_b.setFixedHeight(24)
        self.start_b.clicked.connect(self.start)
        down_set_r_layout.addWidget(self.start_b)

        self.stop_b = QPushButton('Остановить')
        self.stop_b.setEnabled(False)
        self.stop_b.setFixedHeight(24)
        self.stop_b.clicked.connect(self.stop)
        down_set_r_layout.addWidget(self.stop_b)

        self.del_b = QPushButton()
        self.del_b.setFixedSize(30, 24)
        self.del_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/delete.png')))
        self.del_b.clicked.connect(self.delete)
        down_set_r_layout.addWidget(self.del_b)

        set_r_layout.addLayout(down_set_r_layout)

        set_layout.addLayout(set_r_layout)
        layout.addWidget(box)

        self.get_accounts()
        # self.setAutoFillBackground(False)
        # self.setStyleSheet("background-color: #f0f0f0;")

    # def get_rep_id(self):
    #     return self.rep_id

    def get_accounts(self):
        try:
            def on_finish(result):
                self.is_running = False
                account_object.deleteLater()
                self.account_combo.clear()
                for acc in result:
                    self.account_combo.addItem(result[acc]['name'], acc)
                self.status_handler('Информация получена', 3000)

            if not self.is_running:
                self.is_running = True
                wait_loop = QEventLoop()
                account_method = ExchangeRegistry.pro_get(self.exchange, 'get_accounts_ids')
                account_object = AnyMethodObject(account_method, [])
                account_object.finished.connect(on_finish)
                account_object.finished.connect(wait_loop.quit)
                account_object.moveToThread(self.o_tread)
                QMetaObject.invokeMethod(account_object, 'do_work', Qt.ConnectionType.QueuedConnection)
                self.status_handler('Подождите, происходит запрос информации о счетах', 0)
                wait_loop.exec()
                self.instrument_info_update()
        except Exception as e:
            print('step_bot, BotSets, get_accounts ', e)

    def instrument_info_update(self):
        def on_finish(result):
            self.price_label.setText(f'{result[0]} руб')
            self.lot_label.setText(str(result[1]))
            self.status_handler('Информация получена', 3000)
            self.is_running = False
            self.start_b.setEnabled(True)

        if not self.is_running:
            self.is_running = True
            wait_loop = QEventLoop()
            price_lot_method = ExchangeRegistry.pro_get(self.exchange, 'get_price+')
            price_lot_object = AnyMethodObject(price_lot_method, [self.instrument['uid']])
            price_lot_object.finished.connect(on_finish)
            price_lot_object.finished.connect(wait_loop.quit)
            price_lot_object.moveToThread(self.o_tread)
            QMetaObject.invokeMethod(price_lot_object, 'do_work', Qt.ConnectionType.QueuedConnection)
            self.status_handler('Подождите, происходит запрос информации о инструменте', 0)
            wait_loop.exec()

    def start(self):
        try:
            data = self.form_start_data()
            if all(x != 0.0 for x in [data[6], data[7]]):
                self.stop_b.setEnabled(True)
                self.start_b.setEnabled(False)
                self.del_b.setEnabled(False)
                self.startBot.emit({self.rep_id: data})
            else:
                QMessageBox.warning(self, 'Предупреждение', 'Неправильно выставлены настройки', QMessageBox.StandardButton.Ok)
        except Exception as e:
            print(e)

    def form_start_data(self):
        try:
            data = [self.exchange, self.account_combo.currentData(), self.instrument['uid'], int(self.lot_label.text()), self.timeframe.currentData(),
                    self.price.value(), self.step_perc.value(), self.slip_perc.value(), self.order_lot.value(), self.start_buy.value(),
                    self.limit.value(), self.sand_check.isChecked()]
            return data
        except Exception as e:
            print(e)

    def stop(self):
        self.start_b.setEnabled(True)
        self.stop_b.setEnabled(False)
        self.del_b.setEnabled(True)
        self.stopBot.emit(self.rep_id)

    def delete(self):
        self.deleteBot.emit(self.rep_id)

    def get_rep_id(self):
        return self.rep_id

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    def close(self):
        def check():
            if not self.is_running:
                timer.stop()
                self.o_tread.quit()
                self.o_tread.wait()
                wait_loop.quit()

        wait_loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(100)
        timer.timeout.connect(check)
        timer.start()
        wait_loop.exec()


class StepBot(QObject):
    finWork = pyqtSignal()
    doStop = pyqtSignal()

    def __init__(self, name: str, exchange: str, account_id: str, instrument: str, lots: int,
                 interval: Literal[1, 3, 5, 15, 30, 60, 120, 240, 'D', 'W', 'M'], start_price: Decimal,
                 step: Decimal, slip: Decimal, order_lot: int, start_lot: int, limit: int, sand: bool):
        super().__init__()
        self.name = name

        self.exchange = exchange
        self.account_id = account_id

        self.instrument = instrument
        self.lots = lots
        self.start_price = start_price
        self.step = step
        self.slip = slip
        self.order_lot = order_lot
        self.start_lot = start_lot
        self.limit = limit
        self.sand = sand

        self.start_time = None

        self.mem_price = None

        self.strategy_thread = QThread()
        self.strategy_thread.start()

        self.strategy_step = None
        self.strategy_step_wait = False

        self.order_state_thread = QThread()
        self.order_state_thread.start()
        self.order_state_stream = None
        self.order_state_result = None

        self.log = ExchangeRegistry.pro_get('logs', 'bot_log')

        self.post_order = ExchangeRegistry.pro_get(self.exchange, 'post_order')
        self.is_order_fill = ExchangeRegistry.pro_get(self.exchange, 'is_order_fill')
        self.wait_complete = ExchangeRegistry.pro_get(self.exchange, 'get_order_state_stream')
        self.average_position_price = ExchangeRegistry.pro_get(self.exchange, 'get_average_position_price')
        self.get_position_info = ExchangeRegistry.pro_get(self.exchange, 'get_position_info')
        self.cancel_order = ExchangeRegistry.pro_get(self.exchange, 'cancel_order')

        self.doStop.connect(self.stop)

        self.candle_thread = QThread()
        candle_stream_method = ExchangeRegistry.pro_get(self.exchange, 'get_candle_stream')
        self.candle_stream = candle_stream_method(instrument=self.instrument, interval=interval)
        self.candle_stream.newCandle.connect(self.try_new_candle)
        self.candle_stream.finWork.connect(self.on_stream_fin)
        self.candle_stream.moveToThread(self.candle_thread)

        self.candle_thread.started.connect(self.candle_stream.start_work)

    @pyqtSlot()
    def start_work(self):
        self.start_time = datetime.now().strftime('%d_%m_%Y %H-%M-%S')
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
                    order_id_and_status = self.post_order(
                        instrument_id=self.instrument,
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

                if order_id_and_status[0] is not None:
                    def on_order_state(state):
                        print(state)
                        self.order_state_result = state

                    def on_order_stream_fin():
                        self.order_state_stream.deleteLater()
                        self.order_state_stream = None
                        wait_loop.quit()

                    self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                  [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                   str(order_id_and_status[0]),
                                   str(order_id_and_status[1]),
                                   str(self.start_lot),
                                   str(order_id_and_status[2][0]),
                                   str(order_id_and_status[2][1]),
                                   str(order_id_and_status[2][2])])

                    wait_loop = QEventLoop()
                    self.order_state_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=0)
                    self.order_state_stream.sendState.connect(on_order_state)
                    self.order_state_stream.finWork.connect(on_order_stream_fin)
                    self.order_state_stream.moveToThread(self.order_state_thread)
                    QMetaObject.invokeMethod(self.order_state_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                    wait_loop.exec()

                    if self.order_state_result is not None:
                        self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                      [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                       str(order_id_and_status[0]),
                                       str(self.order_state_result[1][1]),
                                       str(self.start_lot),
                                       str(self.order_state_result[1][0] / self.lots / self.start_lot),
                                       str(self.order_state_result[1][2]),
                                       str(self.order_state_result[1][3])])
                    # if self.order_state_result != 0:
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
            self.log.emit(f'{self.name} ¦ {self.start_time}', 'candle',
                          [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                           f'{delta:.4f}',
                           str(self.step),
                           str(candle[4]),
                           f'{self.mem_price:.4f}'])
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
                            order_id_and_status = [None, None, []]

                        # ждём пока заявка не выполнится
                        print(order_id_and_status, 'sell')
                        if order_id_and_status[0] is not None:
                            def on_order_state(state):
                                self.order_state_result = state

                            def on_order_stream_fin():
                                self.order_state_stream.deleteLater()
                                self.order_state_stream = None
                                wait_loop.quit()

                            self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                          [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                           str(order_id_and_status[0]),
                                           str(order_id_and_status[1]).split('.')[1],
                                           str(self.order_lot),
                                           str(order_id_and_status[2][0]),
                                           str(order_id_and_status[2][1]).split('.')[1],
                                           str(order_id_and_status[2][2]).split('.')[1]])

                            print('wait sell')
                            wait_loop = QEventLoop()
                            self.order_state_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=3600)
                            self.order_state_stream.sendState.connect(on_order_state)
                            self.order_state_stream.finWork.connect(on_order_stream_fin)
                            self.order_state_stream.moveToThread(self.order_state_thread)
                            QMetaObject.invokeMethod(self.order_state_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                            print('wait sell, start')
                            wait_loop.exec()
                            print('wait sell, end')

                            if self.order_state_result is not None:
                                self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                              [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                               str(order_id_and_status[0]),
                                               str(self.order_state_result[1][1]).split('.')[1],
                                               str(self.order_lot),
                                               str(self.order_state_result[1][0] / self.lots / self.order_lot),
                                               str(self.order_state_result[1][2]).split('.')[1],
                                               str(self.order_state_result[1][3]).split('.')[1]])

                                if self.order_state_result[0] == 'fill':
                                    self.mem_price = self.order_state_result[1][0] / self.lots / self.order_lot
                                    print(self.mem_price, 'wait sell', self.order_state_result[1][0] / self.lots / self.order_lot)
                                elif self.order_state_result[0] == 'expired':
                                    print(self.mem_price, 'wait sell expir_cancel', self.order_state_result)
                                    self.cancel_order(self.account_id, order_id_and_status[0])
                                else:
                                    print(self.mem_price, 'wait sell cancel', self.order_state_result)
                            else:
                                print(self.mem_price, 'wait sell emerg_cancel', self.order_state_result)
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
                            order_id_and_status = [None, None, []]
                        print(order_id_and_status, 'buy')
                        # ждём пока заявка не выполнится
                        if order_id_and_status[0] is not None:
                            def on_order_state(state):
                                self.order_state_result = state

                            def on_order_stream_fin():
                                self.order_state_stream.deleteLater()
                                self.order_state_stream = None
                                wait_loop.quit()

                            self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                          [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                           str(order_id_and_status[0]),
                                           str(order_id_and_status[1]).split('.')[1],
                                           str(self.order_lot),
                                           str(order_id_and_status[2][0]),
                                           str(order_id_and_status[2][1]).split('.')[1],
                                           str(order_id_and_status[2][2]).split('.')[1]])

                            print('wait buy')
                            wait_loop = QEventLoop()
                            self.order_state_stream = self.wait_complete(order_id=order_id_and_status[0], wait_time=3600)
                            self.order_state_stream.sendState.connect(on_order_state)
                            self.order_state_stream.finWork.connect(on_order_stream_fin)
                            self.order_state_stream.moveToThread(self.order_state_thread)
                            QMetaObject.invokeMethod(self.order_state_stream, 'start_work', Qt.ConnectionType.QueuedConnection)
                            print('wait buy, start')
                            wait_loop.exec()
                            print('wait buy, end')

                            self.log.emit(f'{self.name} ¦ {self.start_time}', 'order',
                                          [datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                           str(order_id_and_status[0]),
                                           str(self.order_state_result[1][1]).split('.')[1],
                                           str(self.order_lot),
                                           str(self.order_state_result[1][0] / self.lots / self.order_lot),
                                           str(self.order_state_result[1][2]).split('.')[1],
                                           str(self.order_state_result[1][3]).split('.')[1]])

                            if self.order_state_result is not None:
                                if self.order_state_result[0] != 'fill':
                                    print(self.mem_price, self.start_price, 'wait buy', self.order_state_result)
                                    if self.order_state_result / self.lots / self.order_lot > self.start_price:
                                        self.mem_price = self.order_state_result / self.lots / self.order_lot
                                    else:
                                        self.mem_price = self.start_price
                                elif self.order_state_result[0] == 'expired':
                                    print(self.mem_price, 'wait buy expir_cancel', self.order_state_result)
                                    self.cancel_order(self.account_id, order_id_and_status[0])
                                else:
                                    print(self.mem_price, 'wait buy cancel', self.order_state_result)
                            else:
                                print(self.mem_price, 'wait buy emerg_cancel', self.order_state_result)
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
        if self.order_state_stream is not None:
            print(7777)
            self.order_state_stream.doStop.emit()
        print(8888)

        def on_strategy_step_fin():
            self.order_state_thread.quit()
            self.order_state_thread.wait()
            self.strategy_step_wait = True
            wait_loop.quit()

        if self.strategy_step is not None:
            wait_loop = QEventLoop()
            self.strategy_step.finished.connect(on_strategy_step_fin)
            wait_loop.exec()
        else:
            self.order_state_thread.quit()
            self.order_state_thread.wait()
            self.strategy_step_wait = True
        print(9999)
        self.strategy_thread.quit()
        print(10101010)
        self.strategy_thread.wait()
        print(11111111)
        self.candle_stream.doStop.emit()
        print(12121212)
