from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QSizePolicy
from elements.VariableDischargesSpinBox import VariableDischargesSpinBox

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class LimitForm(QWidget):
    def __init__(self):
        super().__init__()
        # self.exchange = exchange

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        balance_label = QLabel('Доступный баланс:')
        layout.addWidget(balance_label, 0, 0)

        self.balance = QLabel()
        layout.addWidget(self.balance, 0, 1)

        price_label = QLabel('Цена:')
        layout.addWidget(price_label, 1, 0)

        self.price = VariableDischargesSpinBox('USDT')
        layout.addWidget(self.price, 1, 1)

        quantity_label = QLabel('Количество:')
        layout.addWidget(quantity_label, 2, 0)

        self.quantity = VariableDischargesSpinBox('USDT')
        layout.addWidget(self.quantity, 2, 1)

        cost_label = QLabel('Стоимость ордера:')
        layout.addWidget(cost_label, 3, 0)

        self.cost = QLabel()
        layout.addWidget(self.cost, 3, 1)

        self.setMinimumSize(self.sizeHint())

    def sizeHint(self):
        return self.layout().sizeHint()

    def minimumSizeHint(self):
        return self.layout().minimumSize()


if __name__ == "__main__":
    app = QApplication(argv)
    window = LimitForm()
    window.show()
    exit(app.exec())
