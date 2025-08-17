from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from os.path import dirname, abspath, join
from hashlib import sha256
from json import load


class Auth(QWidget):
    nextSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addStretch(3)

        label = QLabel('Введите пароль:')
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        edit_layout = QHBoxLayout()
        edit_layout.setSpacing(2)
        edit_layout.addStretch(0)

        self.pass_edit = QLineEdit()
        self.pass_edit.setFixedWidth(170)
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.textChanged.connect(self.check_input_fields)
        self.pass_edit.returnPressed.connect(self.handle_enter_key)
        edit_layout.addWidget(self.pass_edit)

        self.eye_button = QPushButton()
        self.eye_button.setFixedWidth(30)
        self.show_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_show.png'))
        self.hide_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_hide.png'))
        self.eye_button.setIcon(self.hide_icon)
        self.eye_button.clicked.connect(self.echo_switch)
        edit_layout.addWidget(self.eye_button)
        edit_layout.addStretch(0)
        layout.addLayout(edit_layout)

        self.enter_button = QPushButton('Войти')
        self.enter_button.setFixedWidth(204)
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.next)
        layout.addWidget(self.enter_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(5)

    def echo_switch(self):
        if self.pass_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.pass_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_button.setIcon(self.show_icon)
        else:
            self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_button.setIcon(self.hide_icon)

    def check_input_fields(self):
        if len(self.pass_edit.text()) > 5:
            self.enter_button.setEnabled(True)
        else:
            self.enter_button.setEnabled(False)

    def handle_enter_key(self):
        self.enter_button.click()

    def next(self):
        with open(join(dirname(abspath(__file__)), '../config.json'), 'r', encoding='utf-8') as json_file:
            config = load(json_file)

        if sha256(self.pass_edit.text().encode()).hexdigest() != config['password']:
            QMessageBox.warning(self, 'Предупреждение', 'Неверный пароль.',
                                QMessageBox.StandardButton.Ok)
            self.pass_edit.setFocus()
        else:
            self.nextSignal.emit(self.pass_edit.text())
