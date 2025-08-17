from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from os.path import dirname, abspath, join
from json import load, dump
from hashlib import sha256
from re import search


class MakePass(QWidget):
    nextSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addStretch(4)

        label = QLabel('Создайте пароль:')
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        form_container = QWidget()
        edit_layout = QFormLayout(form_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)

        pass_layout = QHBoxLayout()
        pass_layout.setSpacing(2)

        self.pass_edit = QLineEdit()
        self.pass_edit.setFixedWidth(170)
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.textChanged.connect(self.check_input_fields)
        self.pass_edit.returnPressed.connect(self.handle_enter_key)
        pass_layout.addWidget(self.pass_edit)

        self.eye_button = QPushButton()
        self.eye_button.setFixedWidth(30)
        self.show_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_show.png'))
        self.hide_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_hide.png'))
        self.eye_button.setIcon(self.hide_icon)
        self.eye_button.clicked.connect(self.echo_switch)
        pass_layout.addWidget(self.eye_button)
        edit_layout.addRow('Пароль <sup>&#9432;</sup> :', pass_layout)
        edit_layout.labelForField(pass_layout).setToolTip('Пароль должен содержать минимум:\n\tодну заглавную букву\n\tодну '
                                                          'цифру\n\tодин специальный символ\n\tбыть длинной более 5 символов')
        repeat_pass_layout = QHBoxLayout()
        repeat_pass_layout.setSpacing(2)

        self.repeat_pass_edit = QLineEdit()
        self.repeat_pass_edit.setFixedWidth(170)
        self.repeat_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.repeat_pass_edit.textChanged.connect(self.check_input_fields)
        self.repeat_pass_edit.returnPressed.connect(self.handle_enter_key)
        repeat_pass_layout.addWidget(self.repeat_pass_edit)

        self.repeat_eye_button = QPushButton()
        self.repeat_eye_button.setFixedWidth(30)
        self.repeat_eye_button.setIcon(self.hide_icon)
        self.repeat_eye_button.clicked.connect(self.echo_switch)
        repeat_pass_layout.addWidget(self.repeat_eye_button)
        edit_layout.addRow('Повторите пароль:', repeat_pass_layout)

        layout.addWidget(form_container,  alignment=Qt.AlignmentFlag.AlignCenter)

        self.enter_button = QPushButton('Подтвердить')
        self.enter_button.setFixedWidth(315)
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.next)
        layout.addWidget(self.enter_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(5)

    def echo_switch(self):
        sender = self.sender()
        if sender == self.eye_button:
            if self.pass_edit.echoMode() == QLineEdit.EchoMode.Password:
                self.eye_button.setIcon(self.show_icon)
                self.pass_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.eye_button.setIcon(self.hide_icon)
                self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            if self.repeat_pass_edit.echoMode() == QLineEdit.EchoMode.Password:
                self.repeat_eye_button.setIcon(self.show_icon)
                self.repeat_pass_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.repeat_eye_button.setIcon(self.hide_icon)
                self.repeat_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def check_input_fields(self):
        if len(self.pass_edit.text()) > 5 and len(self.repeat_pass_edit.text()) > 5:
            self.enter_button.setEnabled(True)
        else:
            self.enter_button.setEnabled(False)

    def handle_enter_key(self):
        if self.sender() == self.pass_edit:
            self.repeat_pass_edit.setFocus()
        elif self.sender() == self.repeat_pass_edit:
            self.enter_button.click()

    def next(self):
        if search(r'\d', self.pass_edit.text()) is None:
            QMessageBox.warning(self, 'Предупреждение', 'Пароль должен включать минимум одну цифру.',
                                QMessageBox.StandardButton.Ok)
            self.repeat_pass_edit.setFocus()
        elif search(r'(?=.*[A-Z]|[А-Я])', self.pass_edit.text()) is None:
            QMessageBox.warning(self, 'Предупреждение', 'Пароль должен включать минимум одну заглавную букву.',
                                QMessageBox.StandardButton.Ok)
            self.repeat_pass_edit.setFocus()
        elif search(r'[!@#$%^&*(),.?":{}|<>]', self.pass_edit.text()) is None:
            QMessageBox.warning(self, 'Предупреждение', 'Пароль должен включать минимум одну специальный символ.',
                                QMessageBox.StandardButton.Ok)
            self.repeat_pass_edit.setFocus()
        elif self.pass_edit.text() != self.repeat_pass_edit.text():
            QMessageBox.warning(self, 'Предупреждение', 'Пароли не совпадают.',
                                QMessageBox.StandardButton.Ok)
            self.repeat_pass_edit.setFocus()
        else:
            with open(join(dirname(abspath(__file__)), '../config.json'), 'r', encoding='utf-8') as json_file:
                config = load(json_file)
                config['password'] = sha256(self.pass_edit.text().encode()).hexdigest()
            with open(join(dirname(abspath(__file__)), '../config.json'), 'w', encoding='utf-8') as json_file:
                dump(config, json_file, indent=4)

            self.nextSignal.emit(self.pass_edit.text())
