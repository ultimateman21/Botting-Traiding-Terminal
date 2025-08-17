from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QGroupBox, QHBoxLayout, QGridLayout, QFormLayout, QLabel, QComboBox, QCheckBox, QFrame, \
    QSpinBox, QMessageBox, QTabWidget, QDialogButtonBox, QDialog, QLineEdit, QFileDialog, QStyle
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEventLoop
from PyQt6.QtGui import QIcon, QPalette, QColor

from os.path import dirname, abspath, join, isfile, splitext, basename
from importlib.util import spec_from_file_location, module_from_spec
from datetime import datetime

from exchanges.exchange_registry import ExchangeRegistry
from elements.StoreAddCombobox import StoreAddCombobox
from st_bots.step_bot import StepBot, BotSets

# from st_bots.tinkoff_step_bot import TinkoffStepBot
# from widgets.bot_sets import BotSets

from PyQt6.QtWidgets import QApplication
from sys import argv, exit

from treads.any_method_tread import AnyMethodThread


class BotTabs(QWidget):
    statusGet = pyqtSignal(str, int)
    startBot = pyqtSignal(list)
    stopBot = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.exchange = None
        self.instrument = None

        self.first_tab_flag = False

        self.bots_repository = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox('Боты')
        tabs_layout = QHBoxLayout(box)
        tabs_layout.setContentsMargins(7, 2, 7, 7)

        corner = QWidget()
        self.instrument = None

        corner_layout = QGridLayout(corner)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setHorizontalSpacing(2)
        corner_layout.setVerticalSpacing(1)

        instrument_combo = StoreAddCombobox()
        instrument_combo.instrumentChange.connect(self.on_instrument_change)
        instrument_combo.statusGet.connect(self.status_handler)
        corner_layout.addWidget(instrument_combo, 0, 0)

        self.new_bot_b = QPushButton()
        self.new_bot_b.setEnabled(False)
        self.new_bot_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/load.png')))
        self.new_bot_b.clicked.connect(self.add_bot)
        corner_layout.addWidget(self.new_bot_b, 0, 1)

        self.strategy_combo = QComboBox()
        # self.strategy_combo.addItem('Step bot', {'bot': TinkoffStepBot, 'sets': BotSets})
        self.strategy_combo.addItem('Step bot', {'bot': StepBot, 'sets': BotSets})
        self.strategy_combo.setFixedHeight(22)
        corner_layout.addWidget(self.strategy_combo, 1, 0)

        self.add_strategy_b = QPushButton()
        # self.new_strategy_b.setFixedHeight(22)
        self.add_strategy_b.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/add.png')))
        self.add_strategy_b.clicked.connect(self.display_add_strategy_dialog)
        corner_layout.addWidget(self.add_strategy_b, 1, 1)

        self.tabs = QTabWidget()
        tab_bar = self.tabs.tabBar()
        self.tabs.addTab(QWidget(), '')
        tab_bar.setStyleSheet('QTabBar::tab {height: 48px;}')
        self.tabs.setCornerWidget(corner, corner=Qt.Corner.TopLeftCorner)
        tabs_layout.addWidget(self.tabs)
        layout.addWidget(box)

        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        if provider not in self.bots_repository:
            self.bots_repository[provider] = {}
        self.exchange = provider
        self.tabs_handler()

    def on_instrument_change(self, instrument: dict):
        self.instrument = instrument
        self.new_bot_b.setEnabled(True)

    def display_add_strategy_dialog(self):
        try:
            def on_file_dialog_b():
                file_name, _ = QFileDialog.getOpenFileName(add_dialog, 'Выбор файла содержащего бота', '', 'Python Files (*.py)')
                if not file_name:
                    return
                path_edit.setText(file_name)

            add_dialog = QDialog(self)
            add_dialog.setWindowTitle('Добавление стратегии')
            add_dialog_layout = QGridLayout(add_dialog)

            name_layout = QFormLayout()
            name_edit = QLineEdit()
            name_layout.addRow('Имя', name_edit)
            add_dialog_layout.addLayout(name_layout, 0, 0)

            file_layout = QFormLayout()
            file_path_layout = QHBoxLayout()

            path_edit = QLineEdit()
            file_path_layout.addWidget(path_edit)

            file_dialog_b = QPushButton('Обзор')
            file_dialog_b.clicked.connect(on_file_dialog_b)
            file_path_layout.addWidget(file_dialog_b)

            file_layout.addRow('Путь к файлу:', file_path_layout)
            add_dialog_layout.addLayout(file_layout, 1, 0, 1, 2)

            bot_name_layout = QFormLayout()
            bot_name_edit = QLineEdit()
            bot_name_layout.addRow('Имя класса бота:', bot_name_edit)
            add_dialog_layout.addLayout(bot_name_layout, 2, 0)

            sets_name_layout = QFormLayout()
            sets_name_edit = QLineEdit()
            sets_name_layout.addRow('Имя класса бота:', sets_name_edit)
            add_dialog_layout.addLayout(sets_name_layout, 2, 1)

            cancel_b = QPushButton('Отмена')
            cancel_b.clicked.connect(add_dialog.reject)
            add_dialog_layout.addWidget(cancel_b, 3, 0)

            apply_b = QPushButton('Подтвердить')
            apply_b.clicked.connect(add_dialog.accept)
            add_dialog_layout.addWidget(apply_b, 3, 1)

            result = add_dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                self.add_strategy(name_edit.text(), path_edit.text(), bot_name_edit.text(), sets_name_edit.text())
        except Exception as e:
            print('BotTabs, display_add_strategy_dialog ', e)

    def add_strategy(self, name: str, file_path: str, bot_name: str, sets_name: str):
        try:
            file_path = abspath(file_path)
            if isfile(file_path):
                module_name = splitext(basename(file_path))[0]

                spec = spec_from_file_location(module_name, file_path)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, bot_name) and hasattr(module, sets_name):
                    bot_cls = getattr(module, bot_name)
                    sets_cls = getattr(module, sets_name)
                    self.strategy_combo.addItem(name, {'bot': bot_cls, 'sets': sets_cls})
                else:
                    self.do_message('Не найдены классы робота и настроек.\nВозможно имена классов указаны не верно.')
                    self.display_add_strategy_dialog()
            else:
                self.do_message('Неверно указан путь к файлу, либо указанный файл не существует.')
                self.display_add_strategy_dialog()
        except Exception as e:
            print('BotTabs, add_strategy ', e)

    def tabs_handler(self):
        allowed_tabs = [i['sets'] for i in self.bots_repository[self.exchange].values()]
        print(allowed_tabs)
        for tab_index in range(self.tabs.count()):
            self.tabs.setTabVisible(tab_index, self.tabs.widget(tab_index) in allowed_tabs)

        self.tabs.setTabVisible(0, not allowed_tabs)

    def add_bot(self):
        try:
            patch_flag = False
            # print([self.instrument, self.strategy_combo.itemText(self.strategy_combo.currentIndex()), self.strategy_combo.itemData(self.strategy_combo.currentIndex())])
            if self.tabs.count() == 1:
                patch_flag = True

            name = self.strategy_combo.itemText(self.strategy_combo.currentIndex())
            contains = self.strategy_combo.itemData(self.strategy_combo.currentIndex())
            rep_id = f"{name} ¦ {self.instrument['ticker']}\n{datetime.now().strftime('%d_%m_%Y %H-%M-%S')}"
            sets = contains['sets'](self.exchange, self.instrument, rep_id)
            sets.startBot.connect(self.start_bot)
            sets.stopBot.connect(self.stop_bot)
            sets.deleteBot.connect(self.delete_bot)
            sets.statusGet.connect(self.status_handler)

            self.bots_repository[self.exchange][rep_id] = {'bot': contains['bot'], 'sets': sets, 'thread': QThread(),
                                                           'worked_bot': None, 'start_time': None}

            self.tabs.addTab(sets, f"{name} ¦ {self.instrument['ticker']}\nОстановлен")
            if patch_flag:
                self.tabs.setTabVisible(0, False)
        except Exception as e:
            print('BotTabs, add_bot ', e)

    def start_bot(self, data: dict):
        print(data)
        rep = self.bots_repository[self.exchange][next(iter(data))]
        thread, bot = rep['thread'], rep['bot'](next(iter(data)).split('\n')[0], *data[next(iter(data))])

        self.bots_repository[self.exchange][next(iter(data))]['worked_bot'] = bot

        bot.moveToThread(thread)
        thread.started.connect(bot.start_work)
        thread.start()

        start_time = datetime.now().strftime('%d_%m_%Y %H-%M-%S')
        index = self.tabs.indexOf(rep['sets'])
        text = self.tabs.tabText(index).split('\n')[0]
        self.tabs.setTabText(index, f'{text}\n{start_time}')
        self.bots_repository[self.exchange][next(iter(data))]['start_time'] = start_time

    def stop_bot(self, rep_id):
        try:
            def on_bot_finish():
                bot.disconnect()
                bot.deleteLater()
                self.bots_repository[self.exchange][rep_id]['worked_bot'] = None
                thread.quit()
                thread.wait()
                wait_loop.quit()

            rep = self.bots_repository[self.exchange][rep_id]
            bot, thread = rep['worked_bot'], rep['thread']

            wait_loop = QEventLoop()
            bot.finWork.connect(on_bot_finish)
            bot.doStop.emit()
            wait_loop.exec()

            index = self.tabs.indexOf(rep['sets'])
            text = self.tabs.tabText(index).split('\n')[0]
            self.tabs.setTabText(index, f'{text}\nОстановлен')
        except Exception as e:
            print('BotTabs, stop_bot ', e)

    def delete_bot(self, rep_id):
        print([rep_id])
        try:
            thread = self.bots_repository[self.exchange][rep_id]['thread']
            set_ = self.bots_repository[self.exchange][rep_id]['sets']
            set_.close()
            set_.disconnect()

            index = self.tabs.indexOf(set_)
            if index != -1:
                self.tabs.removeTab(index)
                self.bots_repository[self.exchange].pop(rep_id)
                set_.deleteLater()
                thread.deleteLater()

                if self.tabs.count() == 1:
                    self.tabs.setTabVisible(0, True)
        except Exception as e:
            print('BotTabs, delete_bot ', e)

    def get_active_bot(self):
        if self.tabs.count() > 1:
            rep_id = self.tabs.currentWidget().get_rep_id()
            rep = self.bots_repository[self.exchange][rep_id]
            return [rep_id.split('\n')[0], rep['start_time']]
        return [None, None]

    def do_message(self, text):
        QMessageBox.warning(self, 'Предупреждение', text, QMessageBox.StandardButton.Ok)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)


if __name__ == "__main__":
    app = QApplication(argv)
    window = BotTabs()
    window.show()
    exit(app.exec())
