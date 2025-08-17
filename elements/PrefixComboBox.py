from PyQt6.QtWidgets import QComboBox, QStyledItemDelegate
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QStandardItemModel, QStandardItem

from PyQt6.QtWidgets import QApplication
from sys import argv, exit


class PrefixComboBox(QComboBox):
    currentTextWithoutPrefixChanged = pyqtSignal(str)

    def __init__(self, prefix=''):
        super().__init__()
        self._prefix = prefix
        self._setup_delegate()
        self._min_width_with_prefix = -1
        self._block_signals = False

        super().currentTextChanged.connect(self._handle_text_changed)

    def _handle_text_changed(self, text):
        if not self._block_signals:
            if self._prefix and text.startswith(self._prefix + ' '):
                text = text[len(self._prefix) + 1:]
            self.currentTextWithoutPrefixChanged.emit(text)

    def _setup_delegate(self):
        class InternalDelegate(QStyledItemDelegate):
            def __init__(self, prefix):
                super().__init__()
                self._prefix = prefix

            def paint(self, painter, option, index):
                original_text = index.data(Qt.ItemDataRole.DisplayRole)
                if self._prefix and original_text.startswith(self._prefix + ' '):
                    original_text = original_text[len(self._prefix) + 1:]

                temp_model = QStandardItemModel()
                item = QStandardItem(original_text)
                temp_model.appendRow(item)
                temp_index = temp_model.index(0, 0)

                super().paint(painter, option, temp_index)

        self.setItemDelegate(InternalDelegate(self._prefix))

    def currentText(self) -> str:
        text = super().currentText()
        if self._prefix and text.startswith(self._prefix + ' '):
            return text[len(self._prefix) + 1:]
        return text

    def minimumSizeHint(self):
        if self._min_width_with_prefix < 0:
            fm = QFontMetrics(self.font())
            max_width = 0
            for i in range(self.count()):
                text = self.itemText(i)
                width = fm.horizontalAdvance(f"{self._prefix} {text}" if self._prefix else text)
                if width > max_width:
                    max_width = width
            self._min_width_with_prefix = max_width + 26
        return QSize(self._min_width_with_prefix, super().minimumSizeHint().height())

    def sizeHint(self):
        return self.minimumSizeHint()

    def paintEvent(self, event):
        current_idx = self.currentIndex()
        if current_idx >= 0:
            original_text = super().currentText()
            if self._prefix and not original_text.startswith(self._prefix + ' '):
                self._block_signals = True
                self.setItemText(current_idx, f'{self._prefix} {original_text}')
                self._block_signals = False

        super().paintEvent(event)
        self._min_width_with_prefix = -1

    # def currentTextChanged(self, text):
    #     if not self._block_signals:
    #         if self._prefix and text.startswith(self._prefix + ' '):
    #             text = text[len(self._prefix) + 1:]
    #         super().currentTextChanged.emit(text)

    def set_prefix(self, prefix):
        self._prefix = prefix
        self._setup_delegate()
        self._min_width_with_prefix = -1
        self.update()

    def addItems(self, texts):
        super().addItems(texts)
        self._min_width_with_prefix = -1

    def clear(self):
        super().clear()
        self._min_width_with_prefix = -1


if __name__ == "__main__":
    app = QApplication(argv)
    window = PrefixComboBox('gppppppppppp')
    window.addItems(['Текущий', 'Все'])
    window.show()
    exit(app.exec())
