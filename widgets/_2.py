import sys
import time
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QThread

# --- Рабочий объект ---
class Worker(QObject):
    @pyqtSlot()
    def do_work(self):
        print(f"[Worker] Начало работы (поток: {QThread.currentThread()})")
        time.sleep(2)  # Эмуляция долгой задачи
        print(f"[Worker] Работа завершена")

# --- Главное окно ---
class MainWindow(QWidget):
    start_work = pyqtSignal()  # сигнал для вызова метода в потоке

    def __init__(self):
        super().__init__()

        self.setWindowTitle("QThread пример")

        self.button = QPushButton("Сделать работу")
        self.label = QLabel("Нажмите кнопку")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # --- Подготовка потока и воркера ---
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        # Связь сигнала с методом в потоке
        self.start_work.connect(self.worker.do_work)

        # Запускаем поток
        self.thread.start()

        # Обработка кнопки
        self.button.clicked.connect(self.on_button_clicked)

    def on_button_clicked(self):
        print(f"[GUI] Кнопка нажата (поток: {QThread.currentThread()})")
        self.label.setText("Работаем...")
        self.start_work.emit()

    def closeEvent(self, event):
        # При закрытии корректно останавливаем поток
        self.thread.quit()
        self.thread.wait()
        event.accept()

# --- Запуск ---
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
