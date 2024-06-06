import sys
import win32gui
import win32con
import win32api
from time import sleep

from PySide6.QtCore import Qt, QMetaObject, QCoreApplication
from PySide6.QtWidgets import QApplication, QMainWindow, QListWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, \
    QLineEdit, QCheckBox, QTextEdit, QWidget, QFrame, QGridLayout, QGroupBox, QSizePolicy


# Qt intellisense pip install PySide6-stubs

from helpers.winapi.windows import get_title


class MainWindow(QMainWindow):
    def __init__(self, peek_window_under_cursor, populate_window_list, start_sending, on_window_select):
        super().__init__()
        self.setWindowTitle("WinApi message test")
        if not self.objectName():
            self.setObjectName(u"QMainWindow")
        self.resize(800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.window_group = QGroupBox("Select window", self.central_widget)
        self.command_group = QGroupBox("Select messages", self.central_widget)
        self.log_text = QTextEdit(self.central_widget)
        self.log_text.setReadOnly(True)
        self.log_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_grid = QGridLayout(self.central_widget)
        self.main_grid.addWidget(self.window_group, 0, 0)
        self.main_grid.addWidget(self.command_group, 0, 1)
        self.main_grid.addWidget(self.log_text, 1, 0, 1, 2, Qt.AlignmentFlag.AlignVCenter)

        # self.window_group.setFrameStyle(QFrame.StyledPanel)
        self.window_listbox = QListWidget(self.window_group)
        self.window_listbox.itemSelectionChanged.connect(on_window_select)
        self.peek_window_button = QPushButton("Peek under cursor", self.window_group)
        self.peek_window_button.clicked.connect(peek_window_under_cursor)
        self.refresh_windows_button = QPushButton("Refresh", self.window_group)
        self.refresh_windows_button.clicked.connect(populate_window_list)

        self.window_layout = QVBoxLayout(self.window_group)
        self.window_layout.addWidget(self.window_listbox)
        self.window_layout.addWidget(self.peek_window_button)
        self.window_layout.addWidget(self.refresh_windows_button)

        # self.command_group.setFrameShape(QFrame.StyledPanel)
        self.key_label = QLabel("Enter Key (Hex):", self.command_group)
        self.key_entry = QLineEdit(self.command_group)
        self.keydown_check = QCheckBox("Key Down", self.command_group)
        self.keydown_check.setChecked(True)
        self.keyup_check = QCheckBox("Key Up", self.command_group)
        self.start_sending_button = QPushButton("Start Sending", self.command_group)
        self.start_sending_button.clicked.connect(start_sending)

        self.command_layout = QVBoxLayout(self.command_group)
        self.command_layout.addWidget(self.key_label)
        self.command_layout.addWidget(self.key_entry)
        self.command_layout.addWidget(self.keydown_check)
        self.command_layout.addWidget(self.keyup_check)
        self.command_layout.addWidget(self.start_sending_button)

        QMetaObject.connectSlotsByName(self)


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.ui = MainWindow(self.peek_window_under_cursor, self.populate_window_list, self.start_sending, self.on_window_select)
        self.ui.show()
        self.last_caption = ""

    def log(self, message):
        self.ui.log_text.append(message)
        self.ui.log_text.ensureCursorVisible()

    def populate_window_list(self):
        window_list = [(hwnd, get_title(hwnd)) for hwnd in self.get_all_hwnds()]
        self.ui.window_listbox.clear()
        for hwnd, title in window_list:
            self.ui.window_listbox.addItem(f"{hwnd} - {title}")

    def get_all_hwnds(self):
        # Function to get all window handles
        def callback(hwnd, hwnds):
            hwnds.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

    def on_window_select(self):
        selected_items = self.ui.window_listbox.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            print(f'Selected item: {selected_item.text()}')

    def peek_window_under_cursor(self):
        self.log('Move cursor around next 10 sec and check log')
        for _ in range(0, 100):
            cursor = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(cursor)
            caption = get_title(hwnd)
            if self.last_caption != caption:
                self.log(f'Hwnd: {hwnd}, caption: {caption}')
                self.last_caption = caption
            sleep(0.1)
        self.log('Peek over')

    def start_sending(self):
        selected_items = self.ui.window_listbox.selectedItems()
        key_hex = self.ui.key_entry.text()
        keydown = self.ui.keydown_check.isChecked()
        keyup = self.ui.keyup_check.isChecked()

        if not selected_items or not key_hex:
            self.log("Please select a window and enter a key.")
            return

        selected_item = selected_items[0]
        hwnd = int(selected_item.text().split(" - ")[0], 16)
        key_hex = int(key_hex, 16)

        self.log(f"Sending messages to window {hwnd} with key {key_hex}")

        def send_messages():
            for _ in range(0, 100):
                if keydown:
                    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_hex, 0)
                    self.log(f"Sent WM_KEYDOWN with {key_hex}")
                if keyup:
                    win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_hex, 0)
                    self.log(f"Sent WM_KEYUP with {key_hex}")
                sleep(1)

        import threading
        threading.Thread(target=send_messages, daemon=True).start()


if __name__ == "__main__":
    app = App()
    sys.exit(app.exec())
