import math
from  datetime import datetime
import sys
import win32gui
import win32con
import win32api
from time import sleep

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QListWidgetItem

from helpers.qt import switch_window_flag
from helpers.winapi.windows import get_title
# Qt intellisense pip install PySide6-stubs
from main_window import MainWindow


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.ui = MainWindow(self.peek_window_under_cursor, self.on_refresh, self.start_sending,
                             self.on_window_select)
        self.ui.show()
        self.last_caption = ""

        self.populate_window_list(hightlight_new=False)

    def log(self, message):
        self.ui.log_text.append(message)
        self.ui.log_text.ensureCursorVisible()

    def sleep_responsively(self, secs):
        QApplication.processEvents()
        sleep(secs)

    def get_all_hwnds(self):
        # Function to get all window handles
        def callback(hwnd, hwnds):
            hwnds.append(hwnd)
            return True
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds

    def on_refresh(self):
        self.populate_window_list()

    # TODO check all TODO
    def populate_window_list(self, hightlight_new=True):
        window_list = [(hwnd, get_title(hwnd)) for hwnd in self.get_all_hwnds()]
        prev_hwnd = {self.ui.window_listbox.item(x).data(Qt.ItemDataRole.UserRole) for x in range(self.ui.window_listbox.count())}
        self.ui.window_listbox.clear()
        for hwnd, title in window_list:
            item = QListWidgetItem(f"{hwnd} - {title}")
            item.setData(Qt.ItemDataRole.UserRole, hwnd)
            if hightlight_new and (hwnd not in prev_hwnd):
                item.setForeground(QColor("red"))
            self.ui.window_listbox.addItem(item)

    def on_window_select(self):
        selected_items = self.ui.window_listbox.selectedItems()
        if selected_items:
            selected_item = selected_items[0]

    def peek_window_under_cursor(self):
        self.populate_window_list()

        with switch_window_flag(self.ui, Qt.WindowStaysOnTopHint, False):
            self.log("Move cursor around next 10 sec and check log.\n Idle 3s to auto select hwnd in the list.\n")
            prev_cursor = win32api.GetCursorPos()
            last_move = datetime.now()

            for _ in range(0, 100):
                cursor = win32api.GetCursorPos()
                hwnd = win32gui.WindowFromPoint(cursor)
                caption = get_title(hwnd)
                if self.last_caption != caption:
                    self.log(f'Hwnd: {hwnd}, caption: {caption}')
                    self.last_caption = caption

                if math.dist(prev_cursor, cursor) > 10:
                    last_move = datetime.now()
                prev_cursor = cursor
                if (datetime.now() - last_move).total_seconds() > 3:
                    items = self.ui.window_listbox.findItems(caption, Qt.MatchFlag.MatchContains)
                    if items:
                        self.ui.window_listbox.setCurrentItem(items[0])

                self.sleep_responsively(0.1)
            self.log('Peek over')

    def send_messages(self, hwnd):
        for _ in range(0, 10):
            key_hex = self.ui.key_entry.text()
            if self.ui.keydown_check.isChecked():
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_hex, 0)
                self.log(f"Sent WM_KEYDOWN with {key_hex}")
            if self.ui.keyup_check.isChecked():
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_hex, 0)
                self.log(f"Sent WM_KEYUP with {key_hex}")
            self.sleep_responsively(1)

        self.log(f"Sent done")

    def start_sending(self):
        selected_items = self.ui.window_listbox.selectedItems()
        key_hex = self.ui.key_entry.text()
        keydown = self.ui.keydown_check.isChecked()
        keyup = self.ui.keyup_check.isChecked()

        if not selected_items or not key_hex:
            self.log("Please select a window and enter a key.")
            return
        selected_item = selected_items[0]
        hwnd = selected_item.data(Qt.ItemDataRole.UserRole)
        key_hex = int(key_hex, 16)

        self.log(f"Sending messages to window {hwnd} with key {key_hex}")
        self.send_messages(hwnd)


if __name__ == "__main__":
    app = App()
    sys.exit(app.exec())
