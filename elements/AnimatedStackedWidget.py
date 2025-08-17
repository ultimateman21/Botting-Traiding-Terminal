from PyQt6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QSize


class AnimatedStackedWidget(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.anim_duration = 300
        self.anim_slot1 = None
        self.anim_slot2 = None
        self.next_index = 0
        self.old_size = QSize()

    def setCurrentIndex(self, index):
        self.next_index = index
        if self.anim_slot1 is not None and self.anim_slot2 is not None:
            self.anim_slot1.stop()
            self.anim_slot2.stop()

        self._start_disappear_animation()

    def _start_disappear_animation(self):
        old_widget = self.currentWidget()
        self.old_size = self.size()

        opacity_effect = QGraphicsOpacityEffect(old_widget)
        old_widget.setGraphicsEffect(opacity_effect)

        self.anim_slot1 = QPropertyAnimation(opacity_effect, b'opacity')
        self.anim_slot1.setDuration(self.anim_duration)
        self.anim_slot1.setStartValue(1.0)
        self.anim_slot1.setEndValue(0.0)
        self.anim_slot1.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim_slot1.finished.connect(self._change_index_and_resize)

        self.anim_slot1.start()

    def _change_index_and_resize(self):
        new_widget = self.widget(self.next_index)
        new_size = new_widget.sizeHint()

        self.anim_slot1 = QPropertyAnimation(self, b'minimumSize')
        self.anim_slot1.setDuration(self.anim_duration)
        self.anim_slot1.setStartValue(self.old_size)
        self.anim_slot1.setEndValue(new_size)

        self.anim_slot2 = QPropertyAnimation(self, b'maximumSize')
        self.anim_slot2.setDuration(self.anim_duration)
        self.anim_slot2.setStartValue(self.old_size)
        self.anim_slot2.setEndValue(new_size)
        self.anim_slot2.finished.connect(self._start_appear_animation)

        self.anim_slot1.start()
        self.anim_slot2.start()

    def _start_appear_animation(self):
        new_widget = self.widget(self.next_index)

        opacity_effect = QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)

        super().setCurrentIndex(self.next_index)

        self.anim_slot1 = QPropertyAnimation(opacity_effect, b'opacity')
        self.anim_slot1.setDuration(self.anim_duration)
        self.anim_slot1.setStartValue(0.0)
        self.anim_slot1.setEndValue(1.0)
        self.anim_slot1.setEasingCurve(QEasingCurve.Type.InQuad)

        self.anim_slot1.start()

    def sizeHint(self):
        if self.currentWidget():
            return self.currentWidget().sizeHint()
        return super().sizeHint()

    def minimumSizeHint(self):
        if self.currentWidget():
            return self.currentWidget().minimumSizeHint()
        return super().minimumSizeHint()
