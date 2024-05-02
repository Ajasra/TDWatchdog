import threading
import os
import socket
import subprocess
import sys
import time
import winshell
import psutil

import select
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QSystemTrayIcon, \
    QMenu, QLabel
from PySide6.QtCore import Signal, QObject, Qt

from Logs.logs import WdLogs
from Settings.Settings import WdSettings


class Communicate(QObject):
    # This class will facilitate thread-safe signals
    received_signal = Signal(str)
    timeout_signal = Signal()


def find_process(app_name, args=None):
    """
    Find the process by name and arguments
    :param app_name:
    :param args:
    :return:
    """
    app_name = app_name.split("\\")[-1]
    found = []
    for process in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        if app_name.lower() in process.info['name'].lower() and (
                args is None or args[0] in process.info['cmdline']):
            found.append([process.info['pid'], process.info['name'], process.info['cmdline']])
    return found


def remove_startup(logging, shortcut_name="watchdog.lnk"):
    """
    Remove the application from the autostart
    :return:
    """
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, shortcut_name)
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
    logging.add_log("Autostart in system removed")


def check_startup(shortcut_name="watchdog.lnk"):
    """
    Check if the application is in the autostart
    :return:
    """
    startup_folder = winshell.startup()
    shortcut_path = os.path.join(startup_folder, shortcut_name)
    return os.path.exists(shortcut_path)


class MainWindow(QWidget):

    logging = None
    settings = None
    kill_button = None
    startup_button = None

    def __init__(self):
        super().__init__()

        self.process = None
        self.pid = None
        self.ping_failures = 0
        self.running = True

        self.comm = Communicate()
        self.comm.received_signal.connect(self.received)
        self.comm.timeout_signal.connect(self.timeout)

        self.init_ui()

        # Create an instance of the WdLogs class and pass the text display widget to it
        self.logging = WdLogs(self.text_display)
        self.settings = WdSettings(self.logging)

        self.setWindowTitle("WatchDog V 0.1")
        self.setGeometry(100, 100, 800, 300)
        self.setWindowIcon(QIcon("Data/icon.ico"))

        if self.settings.get_settings()['autostart']:
            self.start_process()

    def init_ui(self):
        main_layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()
        button_start = QPushButton("Start")
        button_kill = QPushButton("Kill")
        self.kill_button = button_kill
        button_autostart = QPushButton("Add autostart")
        self.startup_button = button_autostart
        # button_close = QPushButton("Close")
        buttons_layout.addWidget(button_start)
        buttons_layout.addWidget(button_kill)
        buttons_layout.addWidget(button_autostart)
        # buttons_layout.addWidget(button_close)

        self.kill_button.setEnabled(False)

        # Connect the "Start" button's clicked signal to startProcess method
        button_start.clicked.connect(self.start_process)  # This line does the connection
        button_kill.clicked.connect(self.kill_process)
        button_autostart.clicked.connect(self.autostart)
        # button_close.clicked.connect(self.close_app)

        # Add buttons layout to main layout
        main_layout.addLayout(buttons_layout)

        self.text_display = QTextEdit("")
        main_layout.addWidget(self.text_display)
        self.text_display.setReadOnly(True)

        # add label at the bottom
        label = QLabel("Author: vasily@sokaris.com")
        label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        main_layout.addWidget(label)

        # Set the main layout
        self.setLayout(main_layout)

        if check_startup():
            self.startup_button.setText("Remove autostart")

    def start_process(self):
        """
        Start the process
        :return:
        """
        temp_set = self.settings.get_settings()
        self.terminate_if_running(temp_set['app'], temp_set['arguments'])

        if self.process is None or self.process.poll() is not None:
            try:
                self.process = subprocess.Popen([temp_set['app']] + temp_set['arguments'])
                if self.process is None:
                    self.logging.add_log("Error starting the process")
                    return
                self.running = True
                self.start_pinging()
                self.logging.add_log("Process started: " + temp_set['app'] + " " + " ".join(temp_set['arguments']))
                self.pid = self.process.pid
                self.logging.add_log("Process PID: " + str(self.process.pid))
                self.kill_button.setEnabled(True)
            except Exception as e:
                self.logging.add_log(f"Error starting the process: {e}")
        else:
            self.logging.add_log("Process is already running")

    def kill_process(self):
        """
        Kill the process
        :return:
        """
        temp_set = self.settings.get_settings()
        self.logging.add_log("Killing the process: " + temp_set['app'])
        try:
            if self.process is not None:
                self.process.terminate()
        except Exception as e:
            self.logging.add_log(f"Error killing the process: {e}")
        self.process = None
        self.pid = None
        self.kill_button.setEnabled(False)
        self.running = False

    def received(self, message):
        """
        Handle the received message
        :param message:
        :return:
        """
        # self.logging.add_only_message("Received message: " + message)
        self.ping_failures = 0

    def timeout(self):
        """
        Handle the timeout
        :return:
        """
        if not self.running:
            # If the process is not running ignore the timeout
            return
        self.ping_failures += 1
        self.logging.add_log(f"Timeout, failures: {self.ping_failures}")
        reboot_value = self.settings.get_settings()['reboot']
        if self.ping_failures >= reboot_value > 0:
            # Reboot the computer if the ping failures are more than the set value
            self.logging.add_log(f"Rebooting the computer after {self.ping_failures} failures")
            self.reboot_computer()
        else:
            self.logging.add_log("Restarting the process")
            self.kill_process()
            self.start_process()

    def start_pinging(self):
        """
        Start the listening thread
        :return:
        """
        def listen_port(instance):
            temp_set = instance.settings.get_settings()
            time.sleep(temp_set['wait'])
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(('localhost', temp_set['ports'][1]))
                s.setblocking(0)
                while instance.running:
                    ready = select.select([s], [], [], temp_set['ping_time'])
                    if ready[0]:
                        data, _ = s.recvfrom(1024)  # Buffer size is 1024 bytes
                        message = data.decode('utf-8')
                        self.comm.received_signal.emit(message)  # Emit the signal
                        time.sleep(2)
                    else:
                        self.comm.timeout_signal.emit()
                        time.sleep(2)
                s.close()

        # Start the listening thread
        thread = threading.Thread(target=listen_port, args=(self,))
        thread.daemon = True  # Ensures the thread will exit when the main program does
        thread.start()

    def reboot_computer(self):
        """
        Reboot the computer
        :return:
        """
        # only works on windows now
        self.logging.add_log("Rebooting the computer")
        os.system('shutdown /r /t 1')

    def close_app(self):
        """
        Close the application
        :return:
        """
        self.running = False
        if self.process is not None:
            self.process.terminate()
        self.close()

    def autostart(self):
        """
        Add or remove autostart of the application in the system
        :return:
        """
        if check_startup():
            remove_startup(self.logging)
            self.startup_button.setText("Add autostart")
        else:
            # get the current location and 'start.bat' file
            app_path = os.path.abspath(sys.argv[0])
            app_name = os.path.basename(app_path)
            app_path = app_path.replace(app_name, "start.bat")

            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, f"watchdog.lnk")
            with winshell.shortcut(shortcut_path) as shortcut:
                shortcut.path = app_path
                shortcut.description = f"Shortcut to {app_name}"
                shortcut.working_directory = os.path.dirname(app_path)
            self.startup_button.setText("Remove autostart")
            self.logging.add_log("Autostart in system added")

    def terminate_if_running(self, app_name, args=None):
        """
        Terminate the process if it is already running
        :param app_name:
        :param args:
        :return:
        """
        processes = find_process(app_name, args)
        if len(processes) > 0:
            # if the process is running, kill it
            self.logging.add_log(f"Process {app_name} is already running, killing it")
            for process in processes:
                try:
                    os.kill(process[0], 9)
                except Exception as e:
                    self.logging.add_log(f"Error killing the process: {e}")
                time.sleep(10)

    def closeEvent(self, event):
        # Override close event to minimize to tray instead of exiting
        event.ignore()
        self.hide()
        self.trayIcon.showMessage("Running", "Application running in the background.", QSystemTrayIcon.Information,
                                  2000)


def create_tray_icon(app, window):
    trayIcon = QSystemTrayIcon(QIcon("Data/icon.ico"), app)
    trayMenu = QMenu()
    openAction = QAction("Open", trayIcon)
    exitAction = QAction("Exit", trayIcon)

    openAction.triggered.connect(window.show)
    exitAction.triggered.connect(app.quit)

    trayMenu.addAction(openAction)
    trayMenu.addAction(exitAction)

    trayIcon.setContextMenu(trayMenu)
    trayIcon.setToolTip("Watchdog 0.1")
    trayIcon.show()
    return trayIcon


if __name__ == "__main__":
    # prevent multiple instances of the application running
    app = QApplication(sys.argv)
    window = MainWindow()
    trayIcon = create_tray_icon(app, window)
    window.trayIcon = trayIcon  # Keep a reference to avoid garbage collection
    window.show()
    app.exec()

