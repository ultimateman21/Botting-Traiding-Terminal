from PyQt6.QtWidgets import QApplication, QTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextOption


class PasswordTextEdit(QTextEdit):
    returnPressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self._real_text = ''
        self._echo_mode = False  # False: Normal, True: Password
        self.textChanged.connect(self._update_real_text)

    def _update_real_text(self):
        if not self._echo_mode:
            self._real_text = self.toPlainText()

    def get_echo_mode(self):
        return self._echo_mode

    def set_echo_mode(self, mode: bool):
        self._echo_mode = mode
        if self._echo_mode:
            self.setPlainText('●' * len(self._real_text))
        else:
            self.setPlainText(self._real_text)
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.returnPressed.emit()

        elif self._echo_mode:
            cursor = self.textCursor()
            if cursor.hasSelection():  # Если есть выделение
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                self._real_text = self._real_text[:start] + self._real_text[end:]
                self.setPlainText('●' * len(self._real_text))
                cursor.setPosition(start)
                self.setTextCursor(cursor)
            elif event.key() == Qt.Key.Key_Backspace:  # Удаление последнего символа
                if self._real_text:
                    cursor_position = cursor.position()
                    self._real_text = self._real_text[:cursor_position - 1] + self._real_text[cursor_position:]
                    self.setPlainText('●' * len(self._real_text))
                    cursor.setPosition(cursor_position - 1)
                    self.setTextCursor(cursor)
            elif event.key() == Qt.Key.Key_Delete:  # Удаление следующего символа
                if self._real_text:
                    cursor_position = cursor.position()
                    self._real_text = self._real_text[:cursor_position] + self._real_text[cursor_position + 1:]
                    self.setPlainText('●' * len(self._real_text))
                    cursor.setPosition(cursor_position)
                    self.setTextCursor(cursor)
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
                text = QApplication.clipboard().text()
                cursor_position = cursor.position()
                self._real_text = (self._real_text[:cursor_position] + text + self._real_text[cursor_position:])
                self.setPlainText('●' * len(self._real_text))
                cursor.setPosition(cursor_position + len(text))
                self.setTextCursor(cursor)
            elif event.text().isprintable():
                cursor_position = cursor.position()
                self._real_text = (self._real_text[:cursor_position] + event.text() + self._real_text[cursor_position:])
                self.setPlainText('●' * len(self._real_text))
                cursor.setPosition(cursor_position + 1)
                self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)

    def get_real_text(self):
        return self._real_text
