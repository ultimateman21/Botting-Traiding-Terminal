from PyQt6.QtWidgets import QWidget, QComboBox, QPushButton, QStyledItemDelegate, QListView, QCompleter, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QRegularExpressionValidator, QIcon, QStandardItem, QFontMetrics
from PyQt6.QtCore import Qt, QSize, QRegularExpression, pyqtSignal

from os.path import dirname, abspath, join
from json import load, dump

from exchanges.exchange_registry import ExchangeRegistry
from treads.any_method_tread import AnyMethodThread

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class StoreAddCombobox(QWidget):
    instrumentChange = pyqtSignal(dict)
    statusGet = pyqtSignal(str, int)

    class CustomDelegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            return QSize(option.rect.width(), 25)

    def __init__(self):
        super().__init__()
        self.purpose = None
        self.tread = None
        self.is_running = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setFixedHeight(22)
        self.combo.setMinimumWidth(106)
        self.combo.setMaxVisibleItems(4)

        self.combo.setView(QListView())
        self.combo.view().setItemDelegate(self.CustomDelegate())

        completer = QCompleter(self.combo.model(), self.combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo.setCompleter(completer)

        validator = QRegularExpressionValidator(QRegularExpression('[A-Z0-9]+'), self)
        self.combo.lineEdit().setValidator(validator)
        self.combo.currentTextChanged.connect(self.check_text)
        self.combo.activated.connect(self.instrument_change)
        self.combo.activated.connect(self.set_tooltip)
        layout.addWidget(self.combo)

        self.add_b = QPushButton()
        self.add_b.setFixedWidth(30)
        self.add_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/deselect.png')))
        self.add_b.clicked.connect(self.check_text)
        layout.addWidget(self.add_b)

        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        try:
            self.purpose = provider
            if self.purpose == 'bybit':
                self.combo.lineEdit().setPlaceholderText('Торговая пара')
            elif self.purpose == 'tinkoff':
                self.combo.lineEdit().setPlaceholderText('Тикер')
            self.load_from_config()
        except Exception as e:
            print('StoreAddCombobox, on_provider_changed ', e)

    def check_text(self):
        try:
            text = self.combo.lineEdit().text()
            if text and self.combo.findText(text) != -1:
                self.add_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/select.png')))
                self.add_b.clicked.disconnect()
                self.add_b.clicked.connect(self.remove)
                self.set_tooltip(self.combo.findText(text))
            else:
                self.add_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/deselect.png')))
                self.add_b.clicked.disconnect()
                self.add_b.clicked.connect(self.add)
                self.combo.setToolTip(None)
        except Exception as e:
            print('StoreAddCombobox, check_text ', e)

    def set_tooltip(self, index: int):
        try:
            if self.purpose == 'tinkoff':
                self.combo.setToolTip(self.combo.itemData(index)['name'])
            elif self.purpose == 'bybit':
                self.combo.setToolTip(self.combo.itemText(index))
        except Exception as e:
            print('StoreAddCombobox, set_tooltip ', e)

    def instrument_change(self):
        try:
            if self.purpose == 'tinkoff':
                self.instrumentChange.emit(self.combo.itemData(self.combo.currentIndex()))
            elif self.purpose == 'bybit':
                self.instrumentChange.emit({'uid': self.combo.itemText(self.combo.currentIndex())})
        except Exception as e:
            print('StoreAddCombobox, instrument_change ', e)

    def add(self):
        try:
            def make_tread(method, params):
                if not self.is_running:
                    self.tread = AnyMethodThread(method, params)
                    self.is_running = True
                    self.tread.finished.connect(on_tread_finish)
                    self.tread.error.connect(on_error)
                    self.tread.start()
                    self.status_handler('Подождите, происходит запрос идентификаторов инструмента', 0)

            def on_tread_finish(data):
                print(data)
                if data is None:
                    QMessageBox.warning(self, 'Предупреждение', f'Такого инструмента не найдено', QMessageBox.StandardButton.Ok)
                else:
                    self.add_item(text, data)
                    self.is_running = False
                    self.dump_2_config()
                    self.check_text()
                    self.instrument_change()
                self.status_handler('Идентификаторы получены', 3000)

            def on_error(error):
                self.statusGet.emit(error)

            text = self.combo.lineEdit().text().strip()
            if text and self.combo.findText(text) == -1:
                if self.purpose == 'tinkoff':
                    ids_get_method = ExchangeRegistry.pro_get('tinkoff', 'get_ids')
                    make_tread(ids_get_method, [text])
                elif self.purpose == 'bybit':
                    self.add_item(text)

                self.dump_2_config()
            self.check_text()
        except Exception as e:
            print('StoreAddCombobox, add ', e)

    def add_item(self, text, item_data: dict = None):
        try:
            item = QStandardItem(text)
            item.setData(item_data, Qt.ItemDataRole.UserRole)
            self.combo.model().appendRow(item)
            self.combo.setCurrentIndex(self.combo.findText(text))

            wight = QFontMetrics(self.combo.view().font()).horizontalAdvance(text)
            if self.combo.size().width() - 30 < wight:
                self.combo.setMinimumWidth(wight + 30)
        except Exception as e:
            print('StoreAddCombobox, add_item ', e)

    def remove(self):
        try:
            text = self.combo.lineEdit().text()
            index = self.combo.findText(text)
            if index != -1:
                self.combo.model().removeRow(index)
                self.dump_2_config()
            self.check_text()
            self.combo.setCurrentIndex(-1)
        except Exception as e:
            print('StoreAddCombobox, remove ', e)

    def dump_2_config(self):
        try:
            with open(join(dirname(abspath(__file__)), '../config.json'), 'r', encoding='utf-8') as json_file:
                config = load(json_file)

            select_dict = {self.combo.itemText(i): self.combo.itemData(i) for i in range(self.combo.count())}
            config[f'{self.purpose}_select'] = select_dict

            with open(join(dirname(abspath(__file__)), '../config.json'), 'w', encoding='utf-8') as json_file:
                dump(config, json_file, indent=4)
        except Exception as e:
            print('StoreAddCombobox, dump_2_config ', e)

    def load_from_config(self):
        try:
            with open(join(dirname(abspath(__file__)), '../config.json'), 'r', encoding='utf-8') as json_file:
                config = load(json_file)
            select_dict = config[f'{self.purpose}_select']
            self.combo.clear()
            for i in select_dict:
                self.add_item(i, select_dict[i])
            self.combo.setCurrentIndex(-1)
        except Exception as e:
            print('StoreAddCombobox, load_from_config ', e)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    def closeEvent(self, event):
        if self.tread is not None and self.tread.isRunning():
            self.tread.terminate()
            self.tread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(argv)
    window = StoreAddCombobox()
    window.show()
    exit(app.exec())
