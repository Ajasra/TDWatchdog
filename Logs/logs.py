import os
import time

from PySide6.QtWidgets import QTextEdit


def create_logs_dir():
    if not os.path.exists('Data'):
        os.mkdir('Data')


class WdLogs:

    def __init__(self, text_display: QTextEdit):
        self.log_file = None
        self.text_display = text_display
        self.logs = ""
        create_logs_dir()
        self.create_log_file()

    def create_log_file(self):
        self.log_file = f'Data/logs_{time.strftime("%m_%d_%Y")}.txt'
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as file:
                file.write("")

    def add_log(self, log: str):
        current_time = time.strftime("%H:%M:%S")
        msg = f"\n{current_time} - {log}"
        self.logs += msg
        self.update_text_display()
        with open(self.log_file, 'a') as file:
            file.write(msg)

    def add_only_message(self, log: str):
        current_time = time.strftime("%H:%M:%S")
        msg = f"\n{current_time} - {log}"
        self.logs += msg
        self.update_text_display()

    def clear_logs(self):
        self.logs = ""
        self.update_text_display()

    def update_text_display(self):
        self.text_display.setText(self.logs)
        self.text_display.verticalScrollBar().setValue(self.text_display.verticalScrollBar().maximum())
