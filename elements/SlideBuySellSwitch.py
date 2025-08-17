from PyQt6.QtCore import pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty, QSize, Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtWidgets import QAbstractButton

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class SlideBuySellSwitch(QAbstractButton):
    stateChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._state = True
        self._position = 1.0

        self.setCheckable(True)
        self.setChecked(True)
        self.clicked.connect(self.animate)

        self.animation = QPropertyAnimation(self, b'position')
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutExpo)
        self.animation.finished.connect(self._update_state)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.repaint()

    def sizeHint(self):
        return QSize(60, 30)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        margin = 1
        r = self.rect().adjusted(0, 0, -1, -1)

        painter.setPen(QPen(QColor('#7A7A7A'), margin))  # Рисуем общую окантовку
        painter.drawRect(r)

        painter.setPen(Qt.PenStyle.NoPen)  # Левый фон
        painter.setBrush(QBrush(QColor('#00CC96')))
        painter.drawRect(QRectF(r.left() + margin, r.top() + margin, r.width() / 2 - margin, r.height() - margin))

        painter.setBrush(QBrush(QColor('#EF553B')))  # Правый фон
        painter.drawRect(QRectF(r.width() / 2, r.top() + margin, r.width() / 2 - margin + 1, r.height() - margin))

        painter.setFont(self.font())  # Шрифт для надписей
        painter.setPen(QPen(QColor('#FFFFFF')))

        on_rect = QRectF(r.x(), r.y(), r.width() / 2, r.height())  # Текст "Купить"
        painter.drawText(on_rect, Qt.AlignmentFlag.AlignCenter, 'Купить')

        off_rect = QRectF(r.x() + r.width() / 2, r.y(), r.width() / 2, r.height())  # Текст "Продать"
        painter.drawText(off_rect, Qt.AlignmentFlag.AlignCenter, 'Продать')

        slider_pos_x = (r.width() / 2 - margin) * self._position  # Позиция ползунка
        sliderRect = QRectF(slider_pos_x + margin, r.y() + margin, r.width() / 2 - margin, r.height() - 2 * margin)

        painter.setPen(QPen(QColor('#ADADAD'), margin))  # Ползунок
        painter.setBrush(QBrush(QColor('#E1E1E1')))
        painter.drawRect(sliderRect)

    def resizeEvent(self, event):
        self.repaint()

    def animate(self, checked):
        if self._state == checked:
            return

        if checked:
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
        else:
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)

        self.animation.start()

    def _update_state(self):
        self._state = bool(round(self._position))
        self.stateChanged.emit(self._state)


if __name__ == "__main__":
    app = QApplication(argv)
    switcher = SlideBuySellSwitch()

    # Подключаемся к сигналу stateChanged
    switcher.stateChanged.connect(lambda state: print(f"Состояние переключателя: {'Купить' if state else 'Продать'}"))

    switcher.show()
    exit(app.exec())
