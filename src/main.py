import threading
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path


from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QWidget
# Qt intellisense pip install PySide6-stubs

from helpers.qt import QListWidgetItemEx, QButtonThread, switch_window_flag
from helpers.winapi.hotkey_events import virtual_code
from helpers.winapi.other import MouseTracker
from helpers.winapi.processes import get_process_windows, filter_process_windows
from src.pick_windows_worker import PickWindowsThread
from src.send_messages_worker import SendMessagesThread
from ui.main_window import MainWindow


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.ui = MainWindow(self.on_peek_windows_under_cursor, self.on_refresh, self.on_start_sending,
                             self.on_window_select, self.on_guess_char)
        self.ui.show()
        self.last_caption = ""
        self.pick_windows_thread = None
        self.send_messages_thread = None

        self.update_hwnd_list(hightlight_new=False)

    @Slot(object)
    def on_ui_lambda(self, on_lambda):
        # this slot is useful to safely shedule any ui operation from different threads
        on_lambda()

    @Slot(str)
    def on_log(self, message):
        self.ui.log_text.append(message)
        # self.ui.log_text.ensureCursorVisible()
        self.ui.log_text.scrollContentsBy(0, self.ui.log_text.contentsMargins().bottom())

    def on_refresh(self):
        self.update_hwnd_list()

    def update_hwnd_list(self, hightlight_new=True, bold_if_visible=True):
        wnds = filter_process_windows(get_process_windows(), remove_invisible=False)
        prev_hwnds = {self.ui.window_listbox.item(x).data(Qt.ItemDataRole.UserRole) for x in
                      range(self.ui.window_listbox.count())}

        self.ui.window_listbox.clear()
        for info in wnds:
            module = Path(info.module_path).name if info.module_path else "-"
            desc = f"{module}   pid: {info.pid}   hwnd: {info.hwnd}   visible: {info.visible}   title: {info.title}"
            item = QListWidgetItemEx(key=info.hwnd,
                                     text=desc,
                                     font_bold=bold_if_visible and info.visible,
                                     font_red=hightlight_new and info.hwnd not in prev_hwnds)
            self.ui.window_listbox.addItem(item)
        self.on_log('Updated')

    def on_window_select(self):
        pass

    def on_guess_char(self, text):
        code = virtual_code(text) if len(text) == 1 else None
        self.ui.code_label.setText(str(code))
        pass

    @Slot(int)
    def on_pick_hwnd(self, hwnd) -> bool:
        items = self.ui.window_listbox.findItems(str(hwnd), Qt.MatchFlag.MatchContains)
        if items:
            self.ui.window_listbox.setCurrentItem(items[0])
            return False
        else:
            self.on_log(f'Item not found, hwnd {hwnd}')

    def on_peek_windows_under_cursor(self):
        self.update_hwnd_list()
        self.pick_windows_thread = PickWindowsThread(btn=self.ui.pick_windows_button,
                                                     contexts=[switch_window_flag(self.ui, Qt.WindowStaysOnTopHint, True)],
                                                     on_pick_hwnd=self.on_pick_hwnd,
                                                     on_log=self.on_log)
        self.pick_windows_thread.start()

    def on_start_sending(self):
        self.send_messages_thread = SendMessagesThread(btn=self.ui.send_messages_button,
                                                       ui=self.ui,
                                                       contexts=[switch_window_flag(self.ui, Qt.WindowStaysOnTopHint, True)],
                                                       on_log=self.on_log)
        self.send_messages_thread.start()


if __name__ == "__main__":
    app = App()
    sys.exit(app.exec())
