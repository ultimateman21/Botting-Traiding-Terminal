import sys
from PyQt6.QtWidgets import QApplication, QAbstractButton
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty, pyqtSlot, QObject, QSize, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QBrush, QLinearGradient, QPalette, QGradient


class QSlideSwitchPrivate(QObject):
    def __init__(self, q):
        super().__init__(q)
        self._position = 0
        self._sliderShape = QRectF()
        self._gradient = QLinearGradient()
        self._gradient.setSpread(QGradient.Spread.PadSpread)
        self._qPointer = q

        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutExpo)

    @pyqtProperty(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self._qPointer.repaint()

    def drawSlider(self, painter):
        margin = 3
        r = self._qPointer.rect().adjusted(0, 0, -1, -1)
        dx = (r.width() - self._sliderShape.width()) * self._position
        sliderRect = self._sliderShape.translated(dx, 0)
        painter.setPen(Qt.PenStyle.NoPen)

        shadow = self._qPointer.palette().color(QPalette.ColorRole.Dark)
        light = self._qPointer.palette().color(QPalette.ColorRole.Light)
        button = self._qPointer.palette().color(QPalette.ColorRole.Button)

        # Внешний фон
        self._gradient.setColorAt(0, shadow.darker(130))
        self._gradient.setColorAt(1, light.darker(130))
        self._gradient.setStart(0, r.height())
        self._gradient.setFinalStop(0, 0)
        painter.setBrush(self._gradient)
        painter.drawRoundedRect(r, 15, 15)

        # Внутренний фон
        self._gradient.setColorAt(0, shadow.darker(140))
        self._gradient.setColorAt(1, light.darker(160))
        self._gradient.setStart(0, 0)
        self._gradient.setFinalStop(0, r.height())
        painter.setBrush(self._gradient)
        painter.drawRoundedRect(r.adjusted(margin, margin, -margin, -margin), 15, 15)

        # Текст под ползунком
        font = self._qPointer.font()
        painter.setFont(font)
        painter.setPen(QPen(light.darker(150)))
        painter.drawText(r, Qt.AlignmentFlag.AlignCenter, "ON  OFF")

        # Ползунок (он будет перекрывать текст)
        self._gradient.setColorAt(0, button.darker(130))
        self._gradient.setColorAt(1, button)
        self._gradient.setStart(0, r.height())
        self._gradient.setFinalStop(0, 0)
        painter.setBrush(self._gradient)
        painter.drawRoundedRect(sliderRect.adjusted(margin, margin, -margin, -margin), 10, 15)

    def updateSliderRect(self, size):
        self._sliderShape.setWidth(size.width() / 2.0)
        self._sliderShape.setHeight(size.height() - 1.0)

    @pyqtSlot(bool, name="animate")
    def animate(self, checked):
        self.animation.setDirection(QPropertyAnimation.Direction.Forward if checked else QPropertyAnimation.Direction.Backward)
        self.animation.start()


class QSlideSwitch(QAbstractButton):
    def __init__(self):
        super().__init__()
        self.d_ptr = QSlideSwitchPrivate(self)
        self.setCheckable(True)
        self.clicked.connect(self.d_ptr.animate)
        self.d_ptr.animation.finished.connect(self.update)

    def sizeHint(self):
        return QSize(60, 30)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.d_ptr.drawSlider(painter)

    def resizeEvent(self, event):
        self.d_ptr.updateSliderRect(event.size())
        self.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    switcher = QSlideSwitch()
    switcher.show()
    sys.exit(app.exec())
