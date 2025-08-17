from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox, QHBoxLayout, QSplitter, QFrame, QLabel, QFormLayout, QSizePolicy, \
    QGridLayout, QComboBox, QCheckBox, QSpinBox, QSpacerItem, QTabBar, QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem, QDateTimeEdit
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMetaObject, QDateTime, QEventLoop

from os.path import dirname, abspath, join

from exchanges.exchange_registry import ExchangeRegistry
from st_bots.tinkoff_step_bot import TinkoffStepBot
from treads.any_method_tread import AnyMethodThread

from widgets.bot_sets import BotSets
from widgets.bot_tabs import BotTabs

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class Bots(QWidget):
    statusGet = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.instrument = None
        self.exchange = None

        self.t_bot_thread = QThread()
        self.t_bot = None
        self.is_running = False

        self.b_bot_thread = QThread()
        self.b_bot = None

        layout = QVBoxLayout(self)

        # self.sets = BotSets()
        # self.sets.statusGet.connect(self.status_handler)
        # self.sets.startBot.connect(self.start_bot)
        # self.sets.stopBot.connect(self.stop_bot)
        # layout.addWidget(self.sets)

        self.bot_tabs = BotTabs()
        self.bot_tabs.statusGet.connect(self.status_handler)
        layout.addWidget(self.bot_tabs)

        port_box = QGroupBox('Портфель')
        port_box.setFixedHeight(200)
        port_layout = QHBoxLayout(port_box)
        port_layout.setContentsMargins(7, 2, 7, 7)

        load_port_b = QPushButton('Запросить портфель')
        load_port_b.clicked.connect(self.get_portfolio)

        self.port = QTabWidget()
        self.port.addTab(QWidget(), '')
        self.port.setCornerWidget(load_port_b, corner=Qt.Corner.TopLeftCorner)
        port_layout.addWidget(self.port)
        layout.addWidget(port_box)

        bot_out_info = QSplitter(orientation=Qt.Orientation.Horizontal)
        bot_out_info.setHandleWidth(7)
        bot_out_info.setStyleSheet('QSplitter::handle:horizontal {background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,'
                                   'stop: 0 transparent, stop: 0.48 transparent, stop: 0.49 #cfcfcf, stop: 0.51 #cfcfcf,'
                                   'stop: 0.52 transparent, stop: 1 transparent); margin-top: 35px; margin-bottom: 35px;}')

        order_box = QGroupBox('Ордеры')
        order_layout = QVBoxLayout(order_box)
        order_layout.setContentsMargins(7, 2, 5, 7)
        order_layout.setSpacing(2)

        self.order_table = QTableWidget(0, 7)
        self.order_table.setHorizontalHeaderLabels(['Время', 'id', 'Статус', 'Лотов', 'Цена', 'Направление', 'Тип'])
        order_layout.addWidget(self.order_table)

        order_control_layout = QHBoxLayout()
        order_control_layout.setSpacing(2)
        order_control_layout.setContentsMargins(0, 0, 0, 0)

        self.order_num = QSpinBox()
        self.order_num.setFixedHeight(22)
        self.order_num.setRange(10, 10000)
        self.order_num.setSingleStep(10)
        self.order_num.setSuffix(' строк')
        order_control_layout.addWidget(self.order_num)

        self.order_b = QPushButton()
        self.order_b.setFixedWidth(30)
        self.order_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/load2.png')))
        self.order_b.clicked.connect(self.bot_info_handler)
        order_control_layout.addWidget(self.order_b)

        order_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        order_control_layout.addItem(order_spacer)

        order_layout.addLayout(order_control_layout)

        bot_out_info.addWidget(order_box)

        candle_box = QGroupBox('Свечи')
        candle_layout = QVBoxLayout(candle_box)
        candle_layout.setContentsMargins(5, 2, 7, 7)
        candle_layout.setSpacing(2)

        self.candle_table = QTableWidget(0, 5)
        self.candle_table.setHorizontalHeaderLabels(['Время', 'Дельта свечи', 'Дельта', 'Цена', 'Сохранённая цена'])
        candle_layout.addWidget(self.candle_table)

        candle_control_layout = QHBoxLayout()
        candle_control_layout.setSpacing(2)
        candle_control_layout.setContentsMargins(0, 0, 0, 0)

        candle_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        candle_control_layout.addItem(candle_spacer)

        self.candle_b = QPushButton()
        self.candle_b.setFixedWidth(30)
        self.candle_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/load3.png')))
        self.candle_b.clicked.connect(self.bot_info_handler)
        candle_control_layout.addWidget(self.candle_b)

        self.candle_num = QSpinBox()
        self.candle_num.setFixedHeight(22)
        self.candle_num.setRange(10, 10000)
        self.candle_num.setSingleStep(10)
        self.candle_num.setSuffix(' строк')
        candle_control_layout.addWidget(self.candle_num)

        candle_layout.addLayout(candle_control_layout)

        bot_out_info.addWidget(candle_box)

        layout.addWidget(bot_out_info, stretch=1)

        self.request_logs = ExchangeRegistry.pro_get('logs', 'request_bot_log')
        self.get_logs = ExchangeRegistry.pro_get('logs', 'get_bot_log')

        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        self.exchange = provider
        # self.price_label.clear()
        # if self.exchange == 'tinkoff':
        #     self.container.setCurrentIndex(0)
        # elif self.exchange == 'bybit':
        #     self.container.setCurrentIndex(1)

    def get_portfolio(self):
        try:
            def make_tread(method, params: list):
                if not self.is_running:
                    self.tread = AnyMethodThread(method, params)
                    self.is_running = True
                    self.tread.finished.connect(on_tread_finish)
                    self.tread.error.connect(on_error)
                    self.tread.start()
                    self.status_handler('Подождите, происходит запрос информации о инструменте', 0)

            def on_tread_finish(data):
                self.make_portfolio(data)
                self.status_handler('Информация получена', 3000)
                self.is_running = False

            def on_error(error):
                self.statusGet.emit(error)

            if self.exchange == 'tinkoff':
                top_ticker_method = ExchangeRegistry.pro_get('tinkoff', 'get_all_portfolio')
                make_tread(top_ticker_method, [])
        except Exception as e:
            print('Bots, get_portfolio ', e)

    def make_portfolio(self, data):
        try:
            def create_table(account_data):
                sh_data = account_data['sh']
                row_count = 4 + len(sh_data)
                table = QTableWidget(row_count, 6)
                table.verticalHeader().setVisible(False)
                table.horizontalHeader().setVisible(False)

                table.setItem(0, 0, QTableWidgetItem('Всего руб'))
                table.setItem(0, 1, QTableWidgetItem('Всего в акциях руб'))

                table.setItem(1, 0, QTableWidgetItem(str(account_data['total'])))
                table.setItem(1, 1, QTableWidgetItem(str(account_data['total_s'])))

                headers = {'ticker': 'Тикер', 'lots': 'Лотов', 'price': 'Цена руб', 'quantity': 'Количество шт',
                           'avg': 'Средняя цена руб', 'block': 'Заблокировано ордерами шт'}
                for col, h in enumerate(headers):
                    table.setItem(3, col, QTableWidgetItem(headers[h]))

                for row_idx, item in enumerate(sh_data, start=4):
                    for col_idx, key in enumerate(headers):
                        val = item.get(key, '')
                        table.setItem(row_idx, col_idx, QTableWidgetItem(str(val)))

                table.resizeColumnsToContents()
                return table

            # Удаляем все вкладки
            while self.port.count():
                self.port.removeTab(0)

            [self.port.addTab(create_table(acc_info['data']), acc_info['name']) for acc_id, acc_info in data.items()]
        except Exception as e:
            print('Bots, make_portfolio ', e)

    def bot_info_handler(self):
        sender = self.sender()
        num, purpose = None, None
        if sender == self.order_b:
            num = self.order_num.value()
            purpose = 'orders'
        elif sender == self.candle_b:
            num = self.order_num.value()
            purpose = 'candles'

        frs, snd = self.bot_tabs.get_active_bot()
        print([frs, snd], 878787)
        if snd is not None:
            def on_get_logs(logs):
                if not logs.empty:
                    order = ['time', 'id', 'status', 'lots', 'price', 'direction', 'type'] if sender == self.order_b else (
                        ['time', 'candle_delta', 'delta', 'price', 'save_price'] if sender == self.candle_b else None)
                    logs = logs[order].values.tolist()

                    if sender == self.order_b:
                        self.order_table.setRowCount(0)
                    elif sender == self.candle_b:
                        self.candle_table.setRowCount(0)

                    for line in logs:
                        if sender == self.order_b:
                            self.new_order(line)
                        elif sender == self.candle_b:
                            self.new_candle(line)
                    if sender == self.order_b:
                        self.order_table.resizeColumnsToContents()
                    elif sender == self.candle_b:
                        self.candle_table.resizeColumnsToContents()

                self.get_logs.disconnect()
                wait_loop.quit()

            log_id = f'{frs} ¦ {snd}'
            wait_loop = QEventLoop()
            self.get_logs.connect(on_get_logs)
            self.request_logs.emit(log_id, purpose, num)
            wait_loop.exec()

    def new_candle(self, data):
        if self.candle_table.rowCount() >= 10000:
            v_scroll = self.candle_table.verticalScrollBar().value()
            h_scroll = self.candle_table.horizontalScrollBar().value()
            self.candle_table.removeRow(0)
            self.candle_table.verticalScrollBar().setValue(v_scroll)
            self.candle_table.horizontalScrollBar().setValue(h_scroll)

        row = self.candle_table.rowCount()
        self.candle_table.insertRow(row)

        [self.candle_table.setItem(row, col, QTableWidgetItem(str(value)))
         for col, value in enumerate(data)]

    def new_order(self, data):
        if self.order_table.rowCount() >= 10000:
            v_scroll = self.order_table.verticalScrollBar().value()
            h_scroll = self.order_table.horizontalScrollBar().value()
            self.order_table.removeRow(0)
            self.order_table.verticalScrollBar().setValue(v_scroll)
            self.order_table.horizontalScrollBar().setValue(h_scroll)

        row = self.order_table.rowCount()
        self.order_table.insertRow(row)

        [self.order_table.setItem(row, col, QTableWidgetItem(str(value)))
         for col, value in enumerate(data)]

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    def closeEvent(self, event):
        # self.sets.close()
        self.t_bot.stop()
        self.t_bot_thread.quit()
        self.t_bot_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(argv)
    window = Bots()
    window.show()
    exit(app.exec())
