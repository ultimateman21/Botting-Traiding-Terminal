from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QComboBox, QLineEdit, QSpacerItem, QSizePolicy
from elements.PrefixComboBox import PrefixComboBox

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class Orders(QWidget):
    def __init__(self):
        super().__init__()

        self.anim_slot1 = None
        self.anim_slot2 = None
        self.collapse = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox('Ордеры')
        sub_layout = QVBoxLayout(box)
        sub_layout.setContentsMargins(5, 5, 5, 5)
        # sub_layout.setContentsMargins(0, 0, 0, 0)

        sort_layout = QHBoxLayout()
        sort_layout.setContentsMargins(0, 0, 0, 0)

        self.type_combo = PrefixComboBox('Тип:')
        self.type_combo.setMaxVisibleItems(3)
        self.type_combo.addItems(['Лимитный', 'Рыночный', 'Все'])
        self.type_combo.currentTextWithoutPrefixChanged.connect(self.change_sort)
        sort_layout.addWidget(self.type_combo)

        self.direction_combo = PrefixComboBox('Направление:')
        self.direction_combo.setMaxVisibleItems(3)
        self.direction_combo.addItems(['Купить', 'Продать', 'Все'])
        self.direction_combo.currentTextWithoutPrefixChanged.connect(self.change_sort)
        sort_layout.addWidget(self.direction_combo)

        self.status_combo = PrefixComboBox('Статус:')
        self.status_combo.setMaxVisibleItems(4)
        self.status_combo.addItems(['Исполненные', 'Отменённые', 'Активные', 'Все'])
        self.status_combo.currentTextWithoutPrefixChanged.connect(self.change_sort)
        sort_layout.addWidget(self.status_combo)

        self.symbol_combo = PrefixComboBox('Инструмент:')
        self.symbol_combo.setMaxVisibleItems(3)
        self.symbol_combo.addItems(['Текущий', 'Все', 'Настраиваемый'])
        self.symbol_combo.currentTextWithoutPrefixChanged.connect(self.change_sort)
        sort_layout.addWidget(self.symbol_combo)

        self.sort_line = QLineEdit()
        # self.sort_line.setMinimumWidth(0)
        self.sort_line.setMaximumWidth(0)
        # self.sort_line.setSizePolicy()
        sort_layout.addWidget(self.sort_line)

        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        sort_layout.addItem(self.spacer)

        sub_layout.addLayout(sort_layout)

        a = ['Тип', 'Тип ордера', 'Направление', 'Цена позиции', 'Количество', 'Объём ордера', 'Комиссия', '', '']
        t = ['currency', 'order_type', 'direction', 'average_position_price', 'lots_requested/lots_executed', 'executed_order_price', 'executed_commission']
        b = []
        sub_layout.addStretch(0)

        layout.addWidget(box)

    def change_sort(self, text):
        sender = self.sender()
        if sender == self.type_combo:
            if text == 'Лимитный':
                pass
            elif text == 'Рыночный':
                pass
            elif text == 'Все':
                pass
        elif sender == self.direction_combo:
            if text == 'Купить':
                pass
            elif text == 'Продать':
                pass
            elif text == 'Все':
                pass
        elif sender == self.status_combo:
            if text == 'Исполненные':
                pass
            elif text == 'Отменённые':
                pass
            elif text == 'Активные':
                pass
            elif text == 'Все':
                pass
        elif sender == self.symbol_combo:
            print([text])
            if text == 'Текущий':
                self.anim_handler('collapse')
            elif text == 'Все':
                self.anim_handler('collapse')
            elif text == 'Настраиваемый':
                self.anim_handler('decollapse')

    def anim_handler(self, type_):
        fin = self.width() - self.type_combo.width() - self.direction_combo.width() - self.status_combo.width() - self.symbol_combo.width() - 36
        if type_ == 'decollapse' and self.collapse:
            def action():
                self.spacer.changeSize(0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                self.sort_line.setMinimumWidth(0)
                self.sort_line.setMaximumWidth(16777215)
                self.sort_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.collapse = False

            self.anim_slot1 = QPropertyAnimation(self.sort_line, b'minimumWidth')
            self.anim_slot1.setDuration(300)
            self.anim_slot1.setStartValue(0)
            self.anim_slot1.setEndValue(fin)

            self.anim_slot2 = QPropertyAnimation(self.sort_line, b'maximumWidth')
            self.anim_slot2.setDuration(300)
            self.anim_slot2.setStartValue(0)
            self.anim_slot2.setEndValue(fin)
            self.anim_slot2.finished.connect(action)

            self.anim_slot1.start()
            self.anim_slot2.start()
        elif type_ == 'collapse' and not self.collapse:
            self.spacer.changeSize(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.collapse = True

            self.anim_slot1 = QPropertyAnimation(self.sort_line, b'minimumWidth')
            self.anim_slot1.setDuration(300)
            self.anim_slot1.setStartValue(fin)
            self.anim_slot1.setEndValue(0)

            self.anim_slot2 = QPropertyAnimation(self.sort_line, b'maximumWidth')
            self.anim_slot2.setDuration(300)
            self.anim_slot2.setStartValue(fin)
            self.anim_slot2.setEndValue(0)

            self.anim_slot1.start()
            self.anim_slot2.start()


if __name__ == "__main__":
    app = QApplication(argv)
    window = Orders()
    window.show()
    exit(app.exec())
