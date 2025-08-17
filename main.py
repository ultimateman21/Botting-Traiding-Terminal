from PyQt6.QtWidgets import QMainWindow, QMenuBar, QStackedWidget, QStatusBar, QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon

from exchanges.exchange_registry import ExchangeRegistry
from exchanges.tinkoff_ import Tinkoff
from exchanges.bybit_ import Bybit

from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad
from base64 import b64decode

from pages.add_tokens import SetAPISets
from pages.create_pass import MakePass
from pages.terminal import Terminal
from pages.settings import Settings
from pages.patch import Patch
from pages.bots import Bots
from pages.auth import Auth

from logger import Logger

from os.path import dirname, abspath, join
from json import load

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Botting Trading Terminal')
        self.setWindowIcon(QIcon(join(dirname(abspath(__file__)), 'source/crop_icon2.png')))

        self.logger = Logger(join(dirname(abspath(__file__)), 'logs'))

        ExchangeRegistry.register_provider('logs')
        ExchangeRegistry.register('logs', 'bot_log', self.logger.botLog)
        ExchangeRegistry.register('logs', 'request_bot_log', self.logger.requestBotLog)
        ExchangeRegistry.register('logs', 'get_bot_log', self.logger.getBotLog)

        self.menu_bar = QMenuBar()
        self.exchange_menu = self.menu_bar.addMenu('Биржа: Не выбрана')

        self.tinkoff_action = self.exchange_menu.addAction(QIcon(join(dirname(abspath(__file__)), 'source/tinkoff.png')), 'T-Инвестиции')
        self.tinkoff_action.triggered.connect(self.exchange_change)
        self.bybit_action = self.exchange_menu.addAction(QIcon(join(dirname(abspath(__file__)), 'source/bybit.png')), 'Bybit (с ограничениями)')
        self.bybit_action.triggered.connect(self.exchange_change)

        self.terminal_menu = self.menu_bar.addAction('Терминал')
        self.terminal_menu.setEnabled(False)
        self.terminal_menu.triggered.connect(self.layout_handler)

        self.bot_menu = self.menu_bar.addAction('Боты')
        self.bot_menu.setEnabled(False)
        self.bot_menu.triggered.connect(self.layout_handler)

        # self.settings_menu = self.menu_bar.addAction('Настройки')
        # self.terminal_menu.setEnabled(False)
        # self.settings_menu.triggered.connect(self.layout_handler)

        self.status_bar = QStatusBar()
        self.status_label = QLabel()
        self.status_label.setContentsMargins(7, 0, 0, 3)
        self.status_bar.addPermanentWidget(self.status_label, 1)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.check()

        self.patch_page = Patch()
        self.central_widget.addWidget(self.patch_page)

        self.terminal = Terminal()
        self.terminal.statusGet.connect(self.status_handler)
        self.central_widget.addWidget(self.terminal)

        self.bots = Bots()
        self.bots.statusGet.connect(self.status_handler)
        self.central_widget.addWidget(self.bots)

        # self.settings = Settings()
        # self.central_widget.addWidget(self.settings)

    def check(self):
        try:
            with open(join(dirname(abspath(__file__)), 'config.json'), 'r', encoding='utf-8') as json_file:
                config = load(json_file)
            if config['password']:
                auth_window = Auth()
                auth_window.nextSignal.connect(self.init_elements)
                self.central_widget.addWidget(auth_window)
            else:
                pass_window = MakePass()
                pass_window.nextSignal.connect(self.pass_create_end)
                self.central_widget.addWidget(pass_window)
        except Exception as e:
            print('MainWindow, check ', e)

    def pass_create_end(self, password):
        try:
            token_window = SetAPISets(password)
            token_window.nextSignal.connect(self.init_elements)

            pass_window = self.central_widget.widget(0)
            self.central_widget.insertWidget(0, token_window)
            self.central_widget.setCurrentIndex(0)

            self.central_widget.removeWidget(pass_window)
            pass_window.deleteLater()
        except Exception as e:
            print('MainWindow, pass_create_end ', e)

    def init_elements(self, password):
        try:
            self.init_exchanges(password)

            self.setMenuBar(self.menu_bar)
            self.setStatusBar(self.status_bar)

            old = self.central_widget.widget(0)
            self.central_widget.removeWidget(old)
            old.deleteLater()
        except Exception as e:
            print('MainWindow, init_elements ', e)

    def init_exchanges(self, password):
        try:
            tokens = self.tokens_decrypt(password)

            tinkoff = Tinkoff(tokens['tinkoff'])
            ExchangeRegistry.register_provider('tinkoff')
            ExchangeRegistry.register('tinkoff', 'get_ids', tinkoff.shares.get_share_ids)
            ExchangeRegistry.register('tinkoff', 'get_top_ticker', tinkoff.get_top_ticker_info)
            ExchangeRegistry.register('tinkoff', 'get_candles', tinkoff.get_candles)
            ExchangeRegistry.register('tinkoff', 'get_candle_stream', tinkoff.get_candle_stream())
            ExchangeRegistry.register('tinkoff', 'get_price+', tinkoff.get_price_l)
            ExchangeRegistry.register('tinkoff', 'get_accounts_ids', tinkoff.get_accounts_ids)
            ExchangeRegistry.register('tinkoff', 'get_all_portfolio', tinkoff.get_all_portfolio)
            ExchangeRegistry.register('tinkoff', 'post_order', tinkoff.post_order)
            ExchangeRegistry.register('tinkoff', 'is_order_fill', tinkoff.is_order_fill)
            ExchangeRegistry.register('tinkoff', 'get_order_state_stream', tinkoff.get_order_state_stream())
            ExchangeRegistry.register('tinkoff', 'get_average_position_price', tinkoff.get_average_position_price)
            ExchangeRegistry.register('tinkoff', 'get_position_info', tinkoff.get_position_info)
            ExchangeRegistry.register('tinkoff', 'cancel_order', tinkoff.cancel_order)

            bybit = Bybit(*tokens['bybit'])
            ExchangeRegistry.register_provider('bybit')
            ExchangeRegistry.register('bybit', 'get_candles', bybit.get_candles)
            ExchangeRegistry.register('bybit', 'get_candle_stream', bybit.CandleStream)
            # ExchangeRegistry.register('bybit', method_name, bybit.method)
        except Exception as e:
            print('MainWindow, init_exchanges ', e)

    @staticmethod
    def tokens_decrypt(password):
        try:
            def decrypt(encrypted, key_):
                cipher = new(key_, MODE_CBC, b64decode(encrypted)[:16])
                return unpad(cipher.decrypt(b64decode(encrypted)[16:]), block_size).decode()

            def process(value, key_):
                if isinstance(value, dict):
                    return {k: decrypt(v, key_) for k, v in value.items()}
                elif isinstance(value, str):
                    return decrypt(value, key_)
                else:
                    return value

            key = PBKDF2(password, b'', dkLen=32, count=100000)
            with open(join(dirname(abspath(__file__)), 'config.json'), 'r', encoding='utf-8') as json_file:
                config = load(json_file)

            return {k: process(v, key) for k, v in config['tokens'].items()}
        except Exception as e:
            print('MainWindow, tokens_decrypt ', e)

    def exchange_change(self):
        try:
            sender = self.sender()
            if sender == self.tinkoff_action:
                ExchangeRegistry.switch_provider('tinkoff')
                self.exchange_menu.setTitle(f"{self.exchange_menu.title().split(':')[0]}: {self.tinkoff_action.text()}")
            elif sender == self.bybit_action:
                ExchangeRegistry.switch_provider('bybit')
                self.exchange_menu.setTitle(f"{self.exchange_menu.title().split(':')[0]}: {self.bybit_action.text()}")
            self.terminal_menu.setEnabled(True)
            self.bot_menu.setEnabled(True)
            # self.settings_menu.setEnabled(True)
            self.patch_page.set_text('Переключитесь на терминал')
            # self.central_widget.setCurrentIndex(0)
        except Exception as e:
            print('MainWindow, exchange_change ', e)

    def layout_handler(self):
        try:
            sender = self.sender()
            if sender == self.terminal_menu:
                self.central_widget.setCurrentIndex(1)
            elif sender == self.bot_menu:
                self.central_widget.setCurrentIndex(2)
            # elif sender == self.settings_menu:
            #     self.central_widget.setCurrentIndex(3)
        except Exception as e:
            print('MainWindow, layout_handler ', e)

    def status_handler(self, message, time):
        self.status_label.setText(message)
        if time != 0:
            QTimer.singleShot(time, self.status_label.clear)

    def closeEvent(self, event):
        self.terminal.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    exit(app.exec())
