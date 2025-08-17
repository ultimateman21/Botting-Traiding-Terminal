from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QDateTimeEdit, QSpinBox, QCheckBox, QPushButton, \
     QGroupBox, QMessageBox, QVBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QObject, QDateTime, pyqtSignal, QThread, QMetaObject, QEventLoop, QMetaMethod, QTimer
from PyQt6.QtGui import QIcon

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel

from plotly.graph_objects import Figure, Candlestick, Bar
from os.path import dirname, abspath, join
from pybit.unified_trading import HTTP

from pandas import DataFrame
from typing import Literal
from json import dumps
from math import ceil

from treads.any_method_tread import AnyMethodThread
from exchanges.exchange_registry import ExchangeRegistry

from PyQt6.QtWidgets import QApplication
from sys import argv, exit
import pandas as pd


class Bridge(QObject):
    initGraph = pyqtSignal(str, str)
    addDataSet = pyqtSignal(str)
    addCandle = pyqtSignal(list)
    clearGraph = pyqtSignal()


class ConsoleJSLogPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f'JS console [{level}]:line {line_number}: {message}')


class Graph(QWidget):
    statusGet = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.exchange = None
        self.instrument = None

        self.graph_init = False

        self.thread = QThread()
        self.thread.start()
        self.tracker = None
        self.tracker_run = False
        self.is_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.graph_box = QGroupBox('График')
        self.graph_layout = QVBoxLayout(self.graph_box)
        self.graph_layout.setContentsMargins(7, 0, 7, 7)

        control_layout = QGridLayout()
        control_layout.setVerticalSpacing(0)

        timeframe_label = QLabel('ТаймФрейм:')
        control_layout.addWidget(timeframe_label, 0, 1)
        self.timeframe_option = QComboBox()
        self.timeframe_option.setMinimumWidth(85)
        self.timeframe_option.setMaxVisibleItems(4)
        frames = [('1 минута', 1), ('3 минуты', 3), ('5 минут', 5), ('15 минут', 15), ('Пол часа', 30),
                  ('1 час', 60), ('2 часа', 120), ('4 часа', 240), ('Сутки', 'D'), ('Неделя', 'W'),
                  ('Месяц', 'M')]
        [self.timeframe_option.addItem(*cor) for cor in frames]
        self.timeframe_option.currentTextChanged.connect(self.check_options)
        control_layout.addWidget(self.timeframe_option, 1, 1)

        from_time_label = QLabel('Промежуток времени от:')
        control_layout.addWidget(from_time_label, 0, 2, 1, 3, alignment=Qt.AlignmentFlag.AlignRight)
        self.from_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.from_time_edit.setFixedHeight(22)
        self.from_time_edit.setDisplayFormat('dd.MM.yyyy  |  HH:mm')
        self.from_time_edit.setCalendarPopup(True)
        control_layout.addWidget(self.from_time_edit, 0, 5)

        self.candle_spin = QSpinBox()
        self.candle_spin.setMinimumWidth(92)
        self.candle_spin.setSingleStep(10)
        self.candle_spin.setSuffix(' свечей')
        self.candle_spin.setRange(100, 720)
        control_layout.addWidget(self.candle_spin, 1, 2)

        self.candle_tracking = QCheckBox()
        self.candle_tracking.setFixedWidth(20)
        self.candle_tracking.setStyleSheet('QCheckBox::indicator {{background-color: white; width: 18px; height: 18px; border: 1px solid black;}}'
                                           'QCheckBox::indicator:checked {{image: url({});}} QCheckBox::indicator:checked:hover {{image: url({});}}'
                                           'QCheckBox::indicator:disabled {{border: 1px solid #cccccc;}}'
                                           'QCheckBox::indicator:hover {{border: 1px solid #0078d7;}}'.format(
                                            join(dirname(abspath(__file__)), '../source/check.png').replace('\\', '/'),
                                            join(dirname(abspath(__file__)), '../source/check_hover.png').replace('\\', '/')))
        self.candle_tracking.setToolTip('Получать свечи в реальном времени')
        control_layout.addWidget(self.candle_tracking, 1, 3)

        to_time_label = QLabel('до:')
        to_time_label.setFixedWidth(17)
        control_layout.addWidget(to_time_label, 1, 4)
        self.to_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.to_time_edit.setFixedHeight(22)
        self.to_time_edit.setDisplayFormat('dd.MM.yyyy  |  HH:mm')
        self.to_time_edit.setCalendarPopup(True)
        control_layout.addWidget(self.to_time_edit, 1, 5)

        self.reset_button = QPushButton()
        self.reset_button.setFixedWidth(30)
        self.reset_button.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/reset.png')))
        self.reset_button.clicked.connect(self.reset_time)
        control_layout.addWidget(self.reset_button, 0, 6)

        self.load_button = QPushButton()
        self.load_button.setEnabled(False)
        self.load_button.setFixedWidth(30)
        self.load_button.setIcon(QIcon(join(dirname(abspath(__file__)), '../source/load.png')))
        self.load_button.clicked.connect(self.set_graph_data)
        control_layout.addWidget(self.load_button, 1, 6)

        self.graph_layout.addLayout(control_layout)

        self.web_view = QWebEngineView()
        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.web_view.setPage(ConsoleJSLogPage(self.web_view))

        self.bridge = Bridge()
        self.web_channel = QWebChannel()
        self.web_channel.registerObject('bridge', self.bridge)
        self.web_view.page().setWebChannel(self.web_channel)

        html = self.load_graph_html()
        self.web_view.setHtml(html)

        self.graph_layout.addWidget(self.web_view)

        layout.addWidget(self.graph_box)
        ExchangeRegistry.signals.providerChanged.connect(self.on_provider_changed)

    def on_provider_changed(self, provider: str):
        try:
            self.exchange = provider
            if self.graph_init:
                self.bridge.clearGraph.emit()
        except Exception as e:
            print('Graph, on_provider_changed ', e)

    def set_instrument(self, instrument: dict):
        try:
            self.instrument = instrument['uid']
            print(self.instrument)
            self.load_button.setEnabled(True)
        except Exception as e:
            print('Graph, set_instrument ', e)

    @staticmethod
    def load_graph_html():
        with open(join(dirname(abspath(__file__)), '../source/graph.html'), 'r', encoding='utf-8') as html_file:
            html = html_file.read()
        return html

    @staticmethod
    def init_graph_data(df: DataFrame):
        try:
            fig = Figure([Candlestick(x=[], open=[], high=[], low=[], close=[], name='Свеча', xaxis='x', yaxis='y'),
                          Bar(x=[], y=[], name='Объём', xaxis='x', yaxis='y2', offsetgroup=1),
                          Bar(x=[], y=[], name='Оборот', xaxis='x', yaxis='y3', offsetgroup=2)])
            layout = dumps(fig.to_dict()['data'])

            fig = Figure([Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'],
                          close=df['close'], name='Свеча', xaxis='x', yaxis='y'),
                          Bar(x=df['timestamp'], y=df['volume'], name='Объём', xaxis='x', yaxis='y2', offsetgroup=1),
                          *([Bar(x=df['timestamp'], y=df['turnover'], name='Оборот', xaxis='x', yaxis='y3', offsetgroup=2)]
                            if 'turnover' in df.columns else [])])
            fig.update_layout(xaxis=dict(type='date', rangeslider=dict(visible=True, autorange=True, yaxis=dict(rangemode='auto')),
                                         gridcolor='#d3d3d3', nticks=11, tickfont=dict(size=9), minor=dict(showgrid=True)),
                              yaxis=dict(type='linear', side='right', domain=[0.2, 1.0], autorange=True, fixedrange=False,
                                         gridcolor='#d3d3d3', nticks=6, tickfont=dict(size=9)),
                              yaxis2=dict(type='linear', side='right', title=dict(text='Объём', font=dict(size=11), standoff=5),
                                          domain=[0, 0.17], autorange=True, gridcolor='#d3d3d3', tickfont=dict(size=9)),
                              yaxis3=dict(type='linear', side='left', title=dict(text='Оборот', font=dict(size=11), standoff=5),
                                          overlaying='y2', showgrid=False, tickfont=dict(size=9)),
                              grid=dict(rows=2, columns=1, subplots=[['xy'], ['xy2']], ygap=0.3, xside='top plot'),
                              margin=dict(t=55, l=5, r=5, b=25), legend=dict(visible=False), hoversubplots='axis',
                              template='ggplot2', hovermode='x')

            return [layout, fig.to_json()]
        except Exception as e:
            print('Graph, init_graph_data ', e)

    def check_options(self):
        if isinstance(self.timeframe_option.currentData(), int):
            self.candle_tracking.setEnabled(True)
        else:
            self.candle_tracking.setChecked(False)
            self.candle_tracking.setEnabled(False)

    def reset_time(self):
        try:
            n_candle = self.candle_spin.value()
            if isinstance(self.timeframe_option.currentData(), int):
                time_ = QDateTime.currentDateTime().addSecs(-60 * self.timeframe_option.currentData() * n_candle)
            elif self.timeframe_option.currentData() == 'D':
                time_ = QDateTime.currentDateTime().addDays(-1 * n_candle)
            elif self.timeframe_option.currentData() == 'W':
                time_ = QDateTime.currentDateTime().addDays(-7 * n_candle)
            else:
                time_ = QDateTime.currentDateTime().addMonths(-1 * n_candle)
            self.from_time_edit.setDateTime(time_)
            self.to_time_edit.setDateTime(QDateTime.currentDateTime())
        except Exception as e:
            print('Graph, reset_time ', e)

    def set_graph_data(self):
        try:
            def make_tread(method, params):
                if not self.is_running:
                    self.tread = AnyMethodThread(method, params)
                    self.is_running = True
                    self.tread.finished.connect(on_tread_finish)
                    self.tread.error.connect(on_error)
                    self.tread.start()
                    self.status_handler('Подождите, происходит запрос свечей для графика', 0)

            def on_tread_finish(data):
                text = (f'Вы пытаетесь загрузить {int(data[2])} свечей, что больше чем максимально '
                        f'допустимое количество в 720. Будет загружено 720 свеч от конечного времени.') if data[0] else ''

                if self.exchange == 'tinkoff':
                    if data[0]:
                        self.do_message(text)
                    df = data[1]
                elif self.exchange == 'bybit':
                    if data[0]:
                        self.do_message(text)
                    df = data[1]

                self.is_running = False
                self.status_handler('Информация получена', 3000)
                # print(df, 666666)
                if self.graph_init:
                    # print([dumps(df.to_dict('list'))], 777777)
                    self.bridge.addDataSet.emit(dumps(df.to_dict('list')))
                else:
                    # print([self.init_graph_data(df)], 66666)
                    self.bridge.initGraph.emit(*self.init_graph_data(df))
                    self.graph_init = True

            def on_error(error):
                self.statusGet.emit(error)

            if self.tracker is not None:
                def on_finish():
                    self.tracker.deleteLater()
                    self.tracker = None
                    QTimer.singleShot(0, wait_loop.quit)

                wait_loop = QEventLoop()
                self.tracker.finWork.connect(on_finish)
                self.tracker.doStop.emit()
                wait_loop.exec()

            if self.candle_tracking.isChecked():
                self.reset_time()

            if self.to_time_edit.dateTime().toMSecsSinceEpoch() < self.from_time_edit.dateTime().toMSecsSinceEpoch():
                self.do_message('Время "до" не может быть меньше чем время "от"')
                return

            if self.exchange == 'tinkoff':
                get_candles_method = ExchangeRegistry.pro_get('tinkoff', 'get_candles')
                make_tread(get_candles_method, [self.instrument, self.timeframe_option.currentData(),
                                                self.from_time_edit.dateTime().toMSecsSinceEpoch(),
                                                self.to_time_edit.dateTime().toMSecsSinceEpoch(), 'single'])
            elif self.exchange == 'bybit':
                get_candles_method = ExchangeRegistry.pro_get('bybit', 'get_candles')
                make_tread(get_candles_method, [self.instrument, self.timeframe_option.currentData(),
                                                self.from_time_edit.dateTime().toMSecsSinceEpoch(),
                                                self.to_time_edit.dateTime().toMSecsSinceEpoch(), 'single'])

            if self.candle_tracking.isChecked():
                stream = ExchangeRegistry.get('get_candle_stream')
                self.tracker = stream(instrument=self.instrument, interval=self.timeframe_option.currentData())
                self.tracker.newCandle.connect(self.add_candle)
                self.tracker.moveToThread(self.thread)
                QMetaObject.invokeMethod(self.tracker, 'start_work', Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            print('Graph, set_graph_data ', e)

    def add_candle(self, line):
        self.bridge.addCandle.emit(line)

    def do_message(self, text):
        QMessageBox.warning(self, 'Предупреждение', text, QMessageBox.StandardButton.Ok)

    def status_handler(self, message: str, time: int):
        self.statusGet.emit(message, time)

    def resizeEvent(self, event):
        self.timeframe_option.setMaximumWidth(self.graph_box.width() // 6)
        self.candle_spin.setMaximumWidth(self.graph_box.width() // 7)

    def closeEvent(self, event):
        if self.tracker is not None:
            loop = QEventLoop()
            self.tracker.finWork.connect(self.tracker.deleteLater)
            self.tracker.finWork.connect(loop.quit)
            self.tracker.doStop.emit()
            loop.exec()
            self.tracker = None

        self.thread.quit()
        self.thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(argv)
    window = Graph()
    window.show()
    exit(app.exec())
