from PyQt6.QtWidgets import QWidget, QGroupBox, QLabel, QStackedWidget, QPushButton, QSpacerItem, QSizePolicy, \
     QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout
from PyQt6.QtCore import Qt, pyqtSignal, QLocale
from PyQt6.QtGui import QIcon

from os.path import dirname, abspath, join

from exchanges.exchange_registry import ExchangeRegistry
from elements.StoreAddCombobox import StoreAddCombobox
from treads.any_method_tread import AnyMethodThread

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class TopPanel(QWidget):
    instrumentChange = pyqtSignal(dict)
    statusGet = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(70)

        self.exchange = None
        self.data_labels = {}
        self.instrument = None

        self.tread = None
        self.is_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_box = QGroupBox('Инструмент')

        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(7, 2, 7, 7)

        sub_layout = QVBoxLayout()
        sub_layout.setSpacing(0)

        self.ticker_combo = StoreAddCombobox()
        self.ticker_combo.statusGet.connect(self.status_handler)
        self.ticker_combo.instrumentChange.connect(self.on_instrument_change)
        sub_layout.addWidget(self.ticker_combo)

        price_layout = QFormLayout()
        price_layout.setContentsMargins(2, 2, 0, 0)

        self.price_label = QLabel()
        self.price_label.setContentsMargins(3, 0, 0, 0)
        self.price_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        price_layout.addRow('Стоимость:', self.price_label)

        sub_layout.addLayout(price_layout)
        top_layout.addLayout(sub_layout)

        self.container = QStackedWidget()
        top_layout.addWidget(self.container)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout.addItem(spacer)

        button = QPushButton()
        button.setFixedWidth(30)
        button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        button.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/reset.png')))
        button.clicked.connect(self.update_data)
        top_layout.addWidget(button)

        layout.addWidget(top_box)

        tinkoff = QWidget()
        tinkoff_layout = QGridLayout(tinkoff)
        tinkoff_layout.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        tinkoff_layout.setHorizontalSpacing(20)
        tinkoff_layout.setVerticalSpacing(10)
        tinkoff_layout.setContentsMargins(0, 0, 0, 0)

        t_labels = ['Min за год', 'Max за год', 'Средний объём за 10 дней', 'Капитализация']
        self.data_labels['tinkoff'] = list((e for n, i in enumerate(t_labels) for ls in [(QLabel(i), QLabel())]
                                            for _ in [tinkoff_layout.addWidget(ls[0], 0, n)] for e in [ls[1]]
                                            for _ in [tinkoff_layout.addWidget(e, 1, n)]))
        self.container.addWidget(tinkoff)

        bybit = QWidget()
        bybit.setStyleSheet('background-color: white')
        bybit_layout = QGridLayout(bybit)
        bybit_layout.setSizeConstraint(QGridLayout.SizeConstraint.SetFixedSize)
        bybit_layout.setHorizontalSpacing(20)
        bybit_layout.setContentsMargins(0, 0, 0, 0)

        b_labels = ['Изменение 24ч', 'Min 24ч', 'Max 24ч', 'Оборот/Объём 24ч']
        self.data_labels['bybit'] = list((e for n, i in enumerate(b_labels) for ls in [(QLabel(i), QLabel())]
                                          for _ in [bybit_layout.addWidget(ls[0], 0, n)] for e in [ls[1]]
                                          for _ in [bybit_layout.addWidget(e, 1, n)]))
        self.container.addWidget(bybit)

        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        try:
            self.exchange = provider
            self.price_label.clear()
            if self.exchange == 'tinkoff':
                self.container.setCurrentIndex(0)
            elif self.exchange == 'bybit':
                self.container.setCurrentIndex(1)
        except Exception as e:
            print('TopPanel, on_provider_changed ', e)

    def on_instrument_change(self, instrument: dict):
        try:
            self.instrument = instrument
            self.update_data()
            self.instrumentChange.emit(instrument)
        except Exception as e:
            print('TopPanel, on_instrument_change ', e)

    def update_data(self):
        try:
            def make_tread(method, params):
                if not self.is_running:
                    self.tread = AnyMethodThread(method, params)
                    self.is_running = True
                    self.tread.finished.connect(on_tread_finish)
                    self.tread.error.connect(on_error)
                    self.tread.start()
                    self.status_handler('Подождите, происходит запрос информации о инструменте', 0)

            def on_tread_finish(data):
                data = {i: QLocale(QLocale.Language.Russian).toString(data[i], 'f', len(str(data[i]).split('.')[1])) for i in data}
                self.price_label.setText(f"{data['price']} руб")
                [lb.setText(f'{data[key]} руб') for lb, key in zip(self.data_labels[self.exchange], ['low', 'high', 'avg', 'cap'])]
                self.status_handler('Информация получена', 3000)
                self.is_running = False

            def on_error(error):
                self.statusGet.emit(error)

            if self.exchange == 'tinkoff':
                top_ticker_method = ExchangeRegistry.pro_get('tinkoff', 'get_top_ticker')
                make_tread(top_ticker_method, [self.instrument['uid'], self.instrument['asset_uid']])

            elif self.exchange == 'bybit':
                # top_ticker_method = ExchangeRegistry.pro_get('bybit', 'get_top_ticker')
                # make_tread(top_ticker_method, [self.instrument['uid'], self.instrument['asset_uid']])
                pass
        except Exception as e:
            print('TopPanel, update_data ', e)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    # def closeEvent(self, event):


if __name__ == "__main__":
    app = QApplication(argv)
    window = TopPanel()
    window.show()
    exit(app.exec())
