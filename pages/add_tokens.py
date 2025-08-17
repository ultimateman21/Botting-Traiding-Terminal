from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad

from os.path import dirname, abspath, join
from base64 import b64encode
from json import load, dump

from elements.PasswordTextEdit import PasswordTextEdit


class SetAPISets(QWidget):
    nextSignal = pyqtSignal(str)

    def __init__(self, pass_):
        super().__init__()
        self.password = pass_

        layout = QVBoxLayout(self)
        layout.addStretch(4)

        label = QLabel('Добавьте API ключи/токены:')
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        form_container = QWidget()
        edit_layout = QFormLayout(form_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)

        bybit_layout = QHBoxLayout()
        bybit_layout.setSpacing(5)

        self.key_edit = QLineEdit()
        self.key_edit.setFixedWidth(140)
        self.key_edit.setPlaceholderText('API ключ')
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.textChanged.connect(self.check_input_fields)
        self.key_edit.returnPressed.connect(self.handle_enter_key)
        bybit_layout.addWidget(self.key_edit)

        sub_layout = QHBoxLayout()
        sub_layout.setSpacing(2)

        self.secret_edit = QLineEdit()
        self.secret_edit.setFixedWidth(270)
        self.secret_edit.setPlaceholderText('API секрет')
        self.secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_edit.textChanged.connect(self.check_input_fields)
        self.secret_edit.returnPressed.connect(self.handle_enter_key)
        sub_layout.addWidget(self.secret_edit)

        self.eye1_button = QPushButton()
        self.eye1_button.setFixedWidth(30)
        self.show_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_show.png'))
        self.hide_icon = QIcon(join(dirname(abspath(__file__)), '../source/eye_hide.png'))
        self.eye1_button.setIcon(self.hide_icon)
        self.eye1_button.clicked.connect(self.echo_switch)
        sub_layout.addWidget(self.eye1_button)

        bybit_layout.addLayout(sub_layout)
        edit_layout.addRow('Bybit:', bybit_layout)

        tinkoff_layout = QHBoxLayout()
        tinkoff_layout.setSpacing(2)

        self.token_edit = PasswordTextEdit()
        self.token_edit.setFixedSize(415, 43)
        self.token_edit.set_echo_mode(True)
        self.token_edit.textChanged.connect(self.check_input_fields)
        self.token_edit.returnPressed.connect(self.handle_enter_key)
        tinkoff_layout.addWidget(self.token_edit)

        self.eye2_button = QPushButton()
        self.eye2_button.setFixedWidth(30)
        self.eye2_button.setIcon(self.hide_icon)
        self.eye2_button.clicked.connect(self.echo_switch)
        tinkoff_layout.addWidget(self.eye2_button)
        edit_layout.addRow('Tinkoff:', tinkoff_layout)

        layout.addWidget(form_container,  alignment=Qt.AlignmentFlag.AlignCenter)

        self.enter_button = QPushButton('Подтвердить')
        self.enter_button.setFixedWidth(495)
        self.enter_button.setEnabled(False)
        self.enter_button.clicked.connect(self.next)
        layout.addWidget(self.enter_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(5)

    def echo_switch(self):
        sender = self.sender()
        if sender == self.eye1_button:
            if self.key_edit.echoMode() == QLineEdit.EchoMode.Password:
                self.eye1_button.setIcon(self.show_icon)
                self.key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
                self.secret_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            else:
                self.eye1_button.setIcon(self.hide_icon)
                self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
                self.secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            if self.token_edit.get_echo_mode():
                self.eye2_button.setIcon(self.show_icon)
                self.token_edit.set_echo_mode(False)
            else:
                self.eye2_button.setIcon(self.hide_icon)
                self.token_edit.set_echo_mode(True)

    def check_input_fields(self):
        if ((len(self.key_edit.text()) > 10 and len(self.secret_edit.text()) > 10)
                or len(self.token_edit.get_real_text()) > 20):
            self.enter_button.setEnabled(True)
        else:
            self.enter_button.setEnabled(False)

    def handle_enter_key(self):
        if self.sender() == self.key_edit:
            self.secret_edit.setFocus()
        elif self.sender() == self.secret_edit:
            self.token_edit.setFocus()
        elif self.sender() == self.token_edit:
            self.enter_button.click()

    def next(self):
        def encrypt(data, key_):
            cipher = new(key_, MODE_CBC)
            encrypted_data = cipher.encrypt(pad(data.encode(), block_size))
            return b64encode(cipher.iv + encrypted_data).decode()

        key = PBKDF2(self.password, b'', dkLen=32, count=100000)
        with open(join(dirname(abspath(__file__)), '../config.json'), 'r', encoding='utf-8') as json_file:
            config = load(json_file)

        if len(self.key_edit.text()) > 10 and len(self.secret_edit.text()) > 10:
            config['tokens']['bybit']['key'] = encrypt(self.key_edit.text(), key)
            config['tokens']['bybit']['secret'] = encrypt(self.secret_edit.text(), key)
        if len(self.token_edit.get_real_text()) > 20:
            config['tokens']['tinkoff'] = encrypt(self.token_edit.get_real_text(), key)

        with open(join(dirname(abspath(__file__)), '../config.json'), 'w', encoding='utf-8') as json_file:
            dump(config, json_file, indent=4)

        self.nextSignal.emit(self.password)
