import sys
from pathlib import Path

# Qt intellisense pip install PySide6-stubs
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

import helpers.os_helpers  # noqa: F401
from src.helpers.qt import QListWidgetItemEx, switch_window_flag, find_by_item_data, Logger, get_selected_data
from src.helpers.winapi.hotkey_events import virtual_code
from src.helpers.winapi.processes import get_process_windows, filter_process_windows
from src.messages import WinMsg, EnumArg
from src.pick_windows_worker import PickWindowsWorker
from src.send_messages_worker import SendMessagesWorker, SendData
from src.ui.main_window import MainWindowFrame, CommandWidget


class MainWindow(MainWindowFrame):
    close_event = Signal()
    send_message_data = Signal(SendData)

    def __init__(self):
        super().__init__()
        self.ui_cw = self.central_widget
        self.ui_cg = self.central_widget.command_group
        self.ui_wg = self.central_widget.window_group

        Logger.instance.log_signal.connect(self.on_log)

        self.ui_wg.window_listbox.itemSelectionChanged.connect(self.on_window_select)
        self.ui_wg.refresh_windows_button.clicked.connect(self.on_refresh)

        def always_on_top():
            return [switch_window_flag(self, Qt.WindowStaysOnTopHint, True)]

        def pick_worker_factory():
            worker = PickWindowsWorker()
            worker.pick_hwnd.connect(self.on_pick_hwnd)
            return worker
        self.ui_wg.pick_windows_button.attach_worker(pick_worker_factory, create_sync_contexts=always_on_top,
                                                     cb_before_worker=self.on_pick_windows_start)

        def send_worker_factory():
            worker = SendMessagesWorker()
            worker.request_send_data.connect(self.on_send_data_request)
            self.send_message_data.connect(worker.on_recieve_data)
            return worker
        self.ui_cg.send_messages_button.attach_worker(send_worker_factory, create_sync_contexts=always_on_top)

        self.update_hwnd_list(hightlight_new=False)

    @Slot(object)
    def on_ui_lambda(self, on_lambda):
        # this slot is useful to safely shedule any ui operation from different threads
        on_lambda()

    @Slot(str)
    def on_log(self, message):
        self.ui_cw.log_text.append(message)
        self.ui_cw.log_text.scrollContentsBy(0, self.ui_cw.log_text.contentsMargins().bottom())

    def on_refresh(self):
        self.update_hwnd_list()

    def update_hwnd_list(self, hightlight_new=True, bold_if_visible=True):
        wnds = filter_process_windows(get_process_windows(), remove_invisible=False)
        prev_len = self.ui_wg.window_listbox.count()
        prev_hwnds = {self.ui_wg.window_listbox.item(x).data(Qt.ItemDataRole.UserRole) for x in
                      range(self.ui_wg.window_listbox.count())}

        self.ui_wg.window_listbox.clear()
        for info in wnds:
            module = Path(info.module_path).name if info.module_path else "-"
            desc = f"{module}  parent: {info.root_parent_hwnd}  pid: {info.pid}" \
                   f"   hwnd: {info.hwnd}   visible: {info.visible}   title: {info.title}"
            if info.root_parent_hwnd:
                desc = '        ' + desc
            item = QListWidgetItemEx(key=info.hwnd,
                                     text=desc,
                                     font_bold=bold_if_visible and info.visible,
                                     font_red=hightlight_new and info.hwnd not in prev_hwnds)
            self.ui_wg.window_listbox.addItem(item)
        count_diff = len(wnds) - prev_len
        Logger.log(f'List of windows updated, changed: {count_diff}.')

    def on_window_select(self):
        pass

    def on_guess_char(self, text):
        code = virtual_code(text) if len(text) == 1 else None
        self.ui_cw.code_label.setText(str(code))
        pass

    @Slot(int)
    def on_pick_hwnd(self, hwnd) -> bool:
        found = find_by_item_data(self.ui_wg.window_listbox, hwnd)
        if len(found) > 2:
            assert False
        elif len(found) == 1:
            self.ui_wg.window_listbox.setCurrentItem(found[0])
            return True
        else:
            Logger.log(f'Item not found, hwnd {hwnd}')
            return False

    def on_pick_windows_start(self):
        self.update_hwnd_list()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.close_event.emit()
        event.accept()

    @Slot()
    def on_send_data_request(self):
        messages = []

        for elem in self.ui_cg.children():
            if not isinstance(elem, CommandWidget):
                continue
            cw: CommandWidget = elem
            if not cw.enabled_check.isChecked():
                continue

            str_arg = cw.str_param_edit.text() if cw.str_param else None
            enum_arg_value = cw.enum_param_dropdown.currentData() if cw.enum_param else None
            messages += [WinMsg(cw.cmd, str_arg, EnumArg([], enum_arg_value))]

        hwnds = get_selected_data(self.ui_wg.window_listbox)
        data = SendData(hwnds, messages)
        self.send_message_data.emit(data)


class App(QApplication):
    def __init__(self):
        super().__init__(sys.argv)

        self.ui = MainWindow()
        self.ui.show()


if __name__ == "__main__":
    app = App()
    sys.exit(app.exec())
