from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        b = QPushButton('fff')
        layout.addWidget(b)
