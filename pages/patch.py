from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class Patch(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        self.label = QLabel('Выберите биржу')
        self.label.setStyleSheet('font-size: 20px; font-weight: bold;')

        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_text(self, text: str):
        self.label.setText(text)
