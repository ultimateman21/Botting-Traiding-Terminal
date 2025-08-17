from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from widgets.graph import Graph
# from widgets._3 import Graph
from widgets.top_panel import TopPanel
from widgets.trade import Trade
from widgets.orders import Orders

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class Terminal(QWidget):
    statusGet = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 5, 7, 2)
        layout.setSpacing(3)

        self.top_panel = TopPanel()
        self.top_panel.statusGet.connect(self.status_handler)
        self.top_panel.instrumentChange.connect(self.on_instrument_change)
        layout.addWidget(self.top_panel)

        sub_layout = QHBoxLayout()
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(7)

        self.graph = Graph()
        self.graph.statusGet.connect(self.status_handler)
        sub_layout.addWidget(self.graph)

        # self.trade = Trade()
        # sub_layout.addWidget(self.trade)

        layout.addLayout(sub_layout)
        #
        # self.orders = Orders()
        # layout.addWidget(self.orders)

    def on_instrument_change(self, instrument: dict):
        try:
            self.graph.set_instrument(instrument)
            # self.trade.set_instrument(instrument)
            # self.orders.set_instrument(instrument)
            pass
        except Exception as e:
            print('Terminal, on_instrument_change ', e)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    # def resizeEvent(self, event):
    #     self.orders.setMinimumHeight((self.height() - self.top_panel.height()) // 4)
    #     self.orders.setMaximumHeight((self.height() - self.top_panel.height()) // 4)

    def closeEvent(self, event):
        self.top_panel.close()
        self.graph.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(argv)
    window = Terminal()
    window.show()
    exit(app.exec())
