import win32api
import win32con
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget

from src.helpers.python_extensions import catch_exceptions, context_switch
from src.helpers.qt import switch_window_flag, QButtonThread
from src.helpers.winapi.hotkey_events import virtual_code
from src.helpers.winapi.other import get_window_info_under_cursor
from src.ui.main_window import MainWindow


class SendMessagesThread(QButtonThread):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    def __init__(self, ui: MainWindow, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = ui

    def get_selected_window(self):
        selected_items = self.ui.window_listbox.selectedItems()

        count = len(selected_items)
        if count == 0:
            return None
        elif count == 1:
            item = selected_items[0]
            return item.data(Qt.ItemDataRole.UserRole)
        else:
            assert False

    def try_send_messages(self):
        hwnd = self.get_selected_window()
        if not hwnd:
            self.log.emit(f'\nNo hwnd selected to test background send: {hwnd}')
            return
        else:
            self.log.emit(f'\nTrying to send to background hwnd: {hwnd}')

        # key_override_str = self.ui.key_entry.text()
        # key_hex = int(key_override_str, 16) if key_override_str else None

        if self.ui.send_down_command.enabled_check.isChecked():
            data = self.ui.send_down_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, data, 0)
            self.log.emit(f"SendMessage WM_KEYDOWN {data}")
            self.msleep(200)

        if self.ui.py_keybd_command.enabled_check.isChecked():
            data = self.ui.py_keybd_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.keybd_event(data, 0, 0, 0)
            self.log.emit(f"keybd_event (down?) {data}")
            self.msleep(200)

        if self.ui.post_down_command.enabled_check.isChecked():
            code = int(self.ui.post_down_command.int_param_edit.text())
            assert code == virtual_code('a')
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, code, 0)
            self.log.emit(f"PostMessage WM_KEYDOWN {code}")
            self.msleep(200)

        if self.ui.send_char_command.enabled_check.isChecked():
            code = int(self.ui.send_char_command.int_param_edit.text())
            win32api.SendMessage(hwnd, win32con.WM_CHAR, code, 0)
            self.log.emit(f"SendMessage WM_CHAR {code}")
            self.msleep(200)

        if self.ui.post_char_command.enabled_check.isChecked():
            code = int(self.ui.post_char_command.int_param_edit.text())
            win32api.PostMessage(hwnd, win32con.WM_CHAR, code, 0)
            self.log.emit(f"PostMessage WM_CHAR {code}")
            self.msleep(200)

        if self.ui.post_up_command.enabled_check.isChecked():
            code = int(self.ui.post_up_command.int_param_edit.text())
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, code, 0)
            self.log.emit(f"PostMessage WM_KEYUP {code}")
            self.msleep(200)

        if self.ui.py_keybd_up_command.enabled_check.isChecked():
            data = self.ui.py_keybd_up_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.keybd_event(data, 0, win32con.KEYEVENTF_KEYUP, 0)
            self.log.emit(f"keybd_event (works only with focus?) KEYEVENTF_KEYUP {data}")
            self.msleep(200)

        if self.ui.send_up_command.enabled_check.isChecked():
            data = self.ui.send_up_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, data, 0)
            self.log.emit(f"SendMessage WM_KEYUP {data}")
            self.msleep(200)

    def run(self):
        self.log.emit(f"Next 10s sending messages to background selected window or \n"
                      f"try to switch window to test foreground send")

        def on_err(e: Exception):
            self.log.emit('Safe_catch: ' + str(e))
        with context_switch(catch_exceptions(on_err), False):
            for _ in range(0, 10):
                self.try_send_messages()
                self.msleep(1000)
        self.log.emit(f"Send over")
