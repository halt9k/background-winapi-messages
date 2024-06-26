import win32api
import win32con
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import QWidget

from src.helpers.python_extensions import catch_exceptions, context_switch
from src.helpers.qt import switch_window_flag, QButtonThread
from src.helpers.virtual_methods import override
from src.helpers.winapi import mouse_events
from src.helpers.winapi.hotkey_events import virtual_code
from src.messages import run_test_message, UiArgs
from src.ui.main_window import CommandWidget, CommandGroup, WindowGroup


class SendMessagesThread(QButtonThread):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    def __init__(self, ui_cg: CommandGroup, ui_wg: WindowGroup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_cg = ui_cg
        self.ui_wg = ui_wg

    def get_selected_window(self):
        selected_items = self.ui_wg.window_listbox.selectedItems()

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
            self.log.emit(f'\nNo hwnd selected')
            return
        else:
            self.log.emit(f'\nTrying to send to hwnd: {hwnd}')

        # key_override_str = self.ui.key_entry.text()
        # key_hex = int(key_override_str, 16) if key_override_str else None
        for elem in self.ui_cg.children():
            if not isinstance(elem, CommandWidget):
                continue
            cw: CommandWidget = elem

            if not cw.enabled_check.isChecked():
                continue

            str_arg = cw.str_param_edit.text() if cw.str_param else None
            enum_arg = cw.enum_param_dropdown.currentData() if cw.enum_param else None
            args = UiArgs(enum_arg, str_arg)

            run_test_message(hwnd, cw.cmd, args)
            self.log.emit(f"{cw.cmd} {args}")
            self.msleep(200)

    @override
    def run(self):
        super().run()
        self.log.emit(f"Next 10s sending messages to background selected window or \n"
                      f"try to switch window to test foreground send")

        def on_err(e: Exception):
            self.log.emit('Safe_catch: ' + str(e))
        with context_switch(catch_exceptions(on_err), False):
            for _ in range(0, 10):
                self.try_send_messages()
                self.msleep(1000)
        self.log.emit(f"Send over")
