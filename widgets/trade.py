from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QGridLayout, QLabel, QStackedWidget, QFrame, QSizePolicy
from elements.SlideBuySellSwitch import SlideBuySellSwitch
from elements.AnimatedStackedWidget import AnimatedStackedWidget
from widgets.LimitForm import LimitForm
from widgets.MarketForm import MarketForm

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class Trade(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(280)
        # self.exchange = exchange

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.trade_box = QGroupBox('Торговля')
        trade_layout = QVBoxLayout(self.trade_box)
        trade_layout.setContentsMargins(7, 2, 7, 7)

        switch_button = SlideBuySellSwitch()
        switch_button.setMinimumHeight(40)
        trade_layout.addWidget(switch_button)

        form_box = QGroupBox()
        over_form_layout = QGridLayout(form_box)
        over_form_layout.setContentsMargins(5, 5, 5, 5)

        type_label = QLabel('Тип заявки:')
        over_form_layout.addWidget(type_label, 0, 0)

        self.type_combo = QComboBox()
        self.type_combo.setMaxVisibleItems(2)
        self.type_combo.addItems(['Лимитный', 'Рыночный'])
        self.type_combo.currentTextChanged.connect(self.change_type)
        over_form_layout.addWidget(self.type_combo, 0, 1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        palette = line.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        line.setPalette(palette)
        over_form_layout.addWidget(line, 1, 0, 1, 2)

        self.order_form = AnimatedStackedWidget()

        self.limit_form = LimitForm()
        self.market_form = MarketForm()

        self.order_form.addWidget(self.limit_form)
        self.order_form.addWidget(self.market_form)

        over_form_layout.addWidget(self.order_form, 2, 0, 1, 2)
        trade_layout.addWidget(form_box)

        layout.addWidget(self.trade_box)
        layout.addStretch(2)

    def change_type(self, type_):
        if type_ == 'Лимитный':
            self.order_form.setCurrentIndex(0)
        elif type_ == 'Рыночный':
            self.order_form.setCurrentIndex(1)


if __name__ == "__main__":
    app = QApplication(argv)
    window = Trade()
    window.show()
    exit(app.exec())
