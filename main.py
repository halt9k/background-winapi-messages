import math
import threading
from  datetime import datetime
import sys
from pathlib import Path

import win32gui
import win32con
import win32api
from time import sleep

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from helpers.python_extensions import ChangeTracker, run_in_thread, safe_catch
from helpers.qt import switch_window_flag, QListWidgetItemEx
from helpers.winapi.hotkey_events import virtual_code
from helpers.winapi.other import MouseTracker, get_window_info_under_cursor
from helpers.winapi.processes import get_process_windows, filter_process_windows
from helpers.winapi.windows import get_title
# Qt intellisense pip install PySide6-stubs
from main_window import MainWindow


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.ui = MainWindow(self.on_peek_windows_under_cursor, self.on_refresh, self.on_start_sending,
                             self.on_window_select, self.on_guess_char)
        self.ui.show()
        self.last_caption = ""
        self.ui_thread = threading.current_thread()

        self.update_hwnd_list(hightlight_new=False)

    def log(self, message):
        self.ui.log_text.append(message)
        self.ui.log_text.ensureCursorVisible()

    def sleep_responsively(self, secs):
        if self.ui_thread == threading.current_thread():
            # TODO extra thread
            # self.log('Warning: sleep in main thread')
            self.processEvents()
        sleep(secs)

    def on_refresh(self):
        self.update_hwnd_list()

    def update_hwnd_list(self, hightlight_new=True, bold_if_visible=True):
        wnds = filter_process_windows(get_process_windows(), remove_invisible=False)
        prev_hwnds = {self.ui.window_listbox.item(x).data(Qt.ItemDataRole.UserRole) for x in range(self.ui.window_listbox.count())}

        self.ui.window_listbox.clear()
        for info in wnds:
            module = Path(info.module_path).name if info.module_path else "-"
            desc = f"{module}   pid: {info.pid}   hwnd: {info.hwnd}   visible: {info.visible}   title: {info.title}"
            item = QListWidgetItemEx(key=info.hwnd,
                                     text=desc,
                                     font_bold=bold_if_visible and info.visible,
                                     font_red=hightlight_new and info.hwnd not in prev_hwnds)
            self.ui.window_listbox.addItem(item)
        self.log('Updated')

    def on_window_select(self):
        pass

    def on_guess_char(self, text):
        code = virtual_code(text) if len(text) == 1 else None
        self.ui.code_label.setText(str(code))
        pass

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

    def check_window_under_cursor(self, mouse_tracker: MouseTracker, window_tracker: ChangeTracker) -> bool:
        changed, (hwnd, title) = window_tracker.track()

        if changed:
            self.log(f'Hwnd: {hwnd}, title: {title}')

        if mouse_tracker.track(10) > 3:
            items = self.ui.window_listbox.findItems(str(hwnd), Qt.MatchFlag.MatchContains)
            if items:
                self.ui.window_listbox.setCurrentItem(items[0])
                return False
            else:
                self.log(f'Item not found, hwnd {hwnd}')

        self.sleep_responsively(0.1)
        return True

    def on_peek_windows_under_cursor(self):
        self.update_hwnd_list()

        self.log("\n"
                 "Move cursor around next 10 sec and check log.\n"
                 "Idle 3s to auto select hwnd in the list.\n")

    # TODO not working
        with safe_catch(), switch_window_flag(self.ui, Qt.WindowStaysOnTopHint, True):
            mouse_tracker = MouseTracker()
            title_tracker = ChangeTracker(get_window_info_under_cursor)

            for _ in range(0, 100):
                if not self.check_window_under_cursor(mouse_tracker, title_tracker):
                    break
        self.log('Pick over')

    def try_send_messages(self):
        if not self.ui.isActiveWindow():
            hwnd, title = get_window_info_under_cursor()
            self.log(f'\nTrying to send to hwnd under cursor: {hwnd}')
        else:
            hwnd = self.get_selected_window()
            if not hwnd:
                self.log(f'\nNo hwnd selected to test background send: {hwnd}')
                return
            else:
                self.log(f'\nTrying to send to background hwnd: {hwnd}')

        # key_override_str = self.ui.key_entry.text()
        # key_hex = int(key_override_str, 16) if key_override_str else None

        if self.ui.keybd_command.enabled_check.isChecked():
            data = self.ui.keybd_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.keybd_event(data, 0, 0, 0)
            self.log(f"keybd_event {data}")

        if self.ui.keydown_command.enabled_check.isChecked():
            int(self.ui.keydown_command.int_param_edit.text())
            key_hex = virtual_code('a')
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_hex, 0)
            self.log(f"PostMessage WM_KEYDOWN {key_hex}")
            self.sleep_responsively(0.2)

        if self.ui.char_command.enabled_check.isChecked():
            key_hex = virtual_code('b')
            win32api.PostMessage(hwnd, win32con.WM_CHAR, key_hex, 0)
            self.log(f"PostMessage WM_KEYDOWN {key_hex}")
            self.sleep_responsively(0.2)

        if self.ui.keyup_command.enabled_check.isChecked():
            key_hex = virtual_code('c')
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_hex, 0)
            self.log(f"PostMessage WM_KEYUP {key_hex}")
            self.sleep_responsively(0.2)

        if self.ui.keybd_command.enabled_check.isChecked():
            data = self.ui.keybd_command.enum_param_dropdown.currentData(Qt.ItemDataRole.UserRole)
            win32api.keybd_event(data, 0, win32con.KEYEVENTF_KEYUP, 0)
            self.log(f"keybd_event (works only with focus?) KEYEVENTF_KEYUP {data}")
            self.sleep_responsively(0.2)

    def on_start_sending(self):
        self.log(f"Next 10s sending messages to background selected window or"
                 f"try to switch window to test foreground send")
        with safe_catch():
            for _ in range(0, 10):
                self.try_send_messages()
                self.sleep_responsively(1)
        self.log(f"Send over")


if __name__ == "__main__":
    app = App()
    sys.exit(app.exec())
