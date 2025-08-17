from PyQt6.QtGui import QKeyEvent, QWheelEvent
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.QtCore import Qt, QLocale

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class VariableDischargesSpinBox(QDoubleSpinBox):
    def __init__(self, cur):
        super().__init__()
        self.setDecimals(6)
        self.setRange(0, 1000000)
        self.setSingleStep(1)
        self.currency = cur
        self.setSuffix(f' {self.currency}')

        self.setLocale(QLocale(QLocale.Language.Russian, QLocale.Country.Russia))

        self.current_digit = 0

        self.line_edit = self.lineEdit()
        self.update_selection()

    def update_selection(self):
        str_value = f'{self.value():.6f}'

        int_part, dec_part = str_value.split('.') if '.' in str_value else (str_value, '')
        idx = self.current_digit if self.current_digit < len(int_part) else len(int_part) + 1 + self.current_digit - len(int_part)

        if 0 <= idx < len(str_value):
            self.line_edit.setSelection(idx, 1)

    def adjust_digit(self, change):
        str_value = f'{self.value():.6f}'

        int_part, dec_part = str_value.split('.') if '.' in str_value else (str_value, '')
        idx = self.current_digit if self.current_digit < len(int_part) else len(int_part) + self.current_digit - len(int_part)
        digits = list(int_part + dec_part)

        if 0 <= idx < len(digits):
            new_digit = int(digits[idx]) + change

            while new_digit > 9 and idx > 0:
                digits[idx] = '0'
                idx -= 1
                new_digit = int(digits[idx]) + 1

            while new_digit < 0 < idx:
                digits[idx] = '9'
                idx -= 1
                new_digit = int(digits[idx]) - 1

            digits[idx] = str(new_digit)

        self.setValue(float(''.join(digits[:len(int_part)]) + '.' + ''.join(digits[len(int_part):])))
        self.update_selection()

    def keyPressEvent(self, event: QKeyEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.current_digit += 1 if event.key() == Qt.Key.Key_Right else -1 if event.key() == Qt.Key.Key_Left else 0
            self.current_digit = max(0, min(self.current_digit, len(str(int(self.value()))) + 5))
            self.update_selection()

        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.adjust_digit(1 if event.key() == Qt.Key.Key_Up else -1)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.current_digit += -1 if event.angleDelta().y() > 0 else 1
            self.current_digit = max(0, min(self.current_digit, len(str(int(self.value()))) + 5))
            self.update_selection()
        else:
            self.adjust_digit(1 if event.angleDelta().y() > 0 else -1)


if __name__ == "__main__":
    app = QApplication(argv)
    window = VariableDischargesSpinBox('USDT')
    window.show()
    exit(app.exec())
