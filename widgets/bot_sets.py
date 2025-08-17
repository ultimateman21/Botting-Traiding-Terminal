from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGroupBox, QHBoxLayout, QGridLayout, QFormLayout, QLabel, QComboBox, QCheckBox, QFrame, \
    QSpinBox, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette, QColor

from os.path import dirname, abspath, join

from elements.VariableDischargesSpinBox import VariableDischargesSpinBox
from exchanges.exchange_registry import ExchangeRegistry
from elements.StoreAddCombobox import StoreAddCombobox

from PyQt6.QtWidgets import QApplication
from sys import argv, exit

from treads.any_method_tread import AnyMethodThread


class BotSets(QWidget):
    statusGet = pyqtSignal(str, int)
    startBot = pyqtSignal(list)
    stopBot = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.exchange = None
        self.instrument = None

        self.thread = None
        self.is_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox('Параметры')
        set_layout = QHBoxLayout(box)
        set_layout.setContentsMargins(7, 2, 7, 7)

        set_l_layout = QGridLayout()
        set_l_layout.setVerticalSpacing(2)

        self.instrument_combo = StoreAddCombobox()
        self.instrument_combo.statusGet.connect(self.status_handler)
        self.instrument_combo.instrumentChange.connect(self.on_instrument_change)
        set_l_layout.addWidget(self.instrument_combo, 0, 0)

        price_layout = QFormLayout()
        price_layout.setHorizontalSpacing(7)
        self.price_label = QLabel()
        # self.price_label.setStyleSheet('background-color: white')
        self.price_label.setMinimumWidth(10)
        price_layout.addRow('Стоимость:', self.price_label)
        set_l_layout.addLayout(price_layout, 0, 1)

        lot_layout = QFormLayout()
        lot_layout.setHorizontalSpacing(7)
        self.lot_label = QLabel()
        # self.lot_label.setStyleSheet('background-color: white')
        self.lot_label.setMinimumWidth(10)
        lot_layout.addRow('Лотность:', self.lot_label)
        set_l_layout.addLayout(lot_layout, 0, 2)

        self.r_button = QPushButton()
        self.r_button.setEnabled(False)
        self.r_button.setFixedSize(30, 24)
        self.r_button.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/reset.png')))
        self.r_button.clicked.connect(self.instrument_info_update)
        set_l_layout.addWidget(self.r_button, 0, 3)

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
        start_price_layout.addRow('Стартовая цена:', self.price)
        set_l_layout.addLayout(start_price_layout, 1, 1, 1, 2)

        self.sand_check = QCheckBox()
        self.sand_check.setFixedWidth(20)
        self.sand_check.setStyleSheet('QCheckBox::indicator {{background-color: white; width: 18px; height: 18px; border: 1px solid black;}}'
                                      'QCheckBox::indicator:checked {{image: url({});}} QCheckBox::indicator:checked:hover {{image: url({});}}'
                                      'QCheckBox::indicator:disabled {{border: 1px solid #cccccc;}}'
                                      'QCheckBox::indicator:hover {{border: 1px solid #0078d7;}}'.format(
                                       join(dirname(abspath(__file__)), '../source/check.png').replace('\\', '/'),
                                       join(dirname(abspath(__file__)), '../source/check_hover.png').replace('\\', '/')))
        self.sand_check.setToolTip('Песочница')
        set_l_layout.addWidget(self.sand_check, 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)

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
        step_layout.addRow('Шаг:', self.step_perc)
        up_set_r_layout.addLayout(step_layout)

        slip_layout = QFormLayout()
        self.slip_perc = VariableDischargesSpinBox('%')
        slip_layout.addRow('Проскальзывание:', self.slip_perc)
        up_set_r_layout.addLayout(slip_layout)

        order_lot_layout = QFormLayout()
        self.order_lot = QSpinBox()
        self.order_lot.setRange(1, 10000)
        order_lot_layout.addRow('Лотов на ордер:', self.order_lot)
        up_set_r_layout.addLayout(order_lot_layout)

        set_r_layout.addLayout(up_set_r_layout)

        down_set_r_layout = QHBoxLayout()
        down_set_r_layout.setSpacing(7)

        start_buy_layout = QFormLayout()
        self.start_buy = QSpinBox()
        self.start_buy.setSuffix(' лотов')
        self.start_buy.setRange(0, 10000)
        self.start_buy.setSpecialValueText('не покупать')
        start_buy_layout.addRow('Купить при пуске:', self.start_buy)
        down_set_r_layout.addLayout(start_buy_layout)

        limit_layout = QFormLayout()
        self.limit = QSpinBox()
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

        set_r_layout.addLayout(down_set_r_layout)

        set_layout.addLayout(set_r_layout)
        layout.addWidget(box)

        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        self.exchange = provider

    def on_instrument_change(self, instrument: dict):
        self.instrument = instrument
        self.r_button.setEnabled(True)
        self.instrument_info_update()

    def instrument_info_update(self):
        def make_tread(method, params):
            if not self.is_running:
                self.tread = AnyMethodThread(method, params)
                self.is_running = True
                self.tread.finished.connect(on_tread_finish)
                self.tread.error.connect(on_error)
                self.tread.start()
                self.status_handler('Подождите, происходит запрос информации о инструменте', 0)

        def on_tread_finish(data):
            self.price_label.setText(f'{data[0]} руб')
            self.lot_label.setText(str(data[1]))
            self.status_handler('Информация получена', 3000)
            self.is_running = False
            self.start_b.setEnabled(True)

        def on_error(error):
            self.statusGet.emit(error)

        if self.exchange == 'tinkoff':
            top_ticker_method = ExchangeRegistry.pro_get('tinkoff', 'get_price+')
            make_tread(top_ticker_method, [self.instrument['uid']])

    def start(self):
        try:
            data = self.form_start_data()
            if all(x != 0.0 for x in [data[4], data[5]]) and data[0] is not None:
                self.stop_b.setEnabled(True)
                self.start_b.setEnabled(False)
                self.startBot.emit(data)
            else:
                QMessageBox.warning(self, 'Предупреждение', 'Неправильно выставлены настройки', QMessageBox.StandardButton.Ok)
        except Exception as e:
            print(e)

    def form_start_data(self):
        try:
            data = [self.instrument['uid'], int(self.lot_label.text()), self.timeframe.currentData(), self.price.value(),
                    self.step_perc.value(), self.slip_perc.value(), self.order_lot.value(), self.start_buy.value(),
                    self.limit.value(), self.sand_check.isChecked()]
            return data
        except Exception as e:
            print(e)

    def stop(self):
        self.start_b.setEnabled(True)
        self.stop_b.setEnabled(False)
        self.stopBot.emit()

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)


if __name__ == "__main__":
    app = QApplication(argv)
    window = BotSets()
    window.show()
    exit(app.exec())
