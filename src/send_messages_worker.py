from PySide6.QtCore import Slot

from src.helpers.python_extensions import catch_exceptions, context_switch
from src.helpers.qt import get_selected_data, log
from src.helpers.qt_async_button import QReusableWorker
from src.helpers.virtual_methods import override
from src.messages import run_test_message, UiArgs
from src.ui.main_window import CommandWidget, CommandGroup, WindowGroup


class SendMessagesWorker(QReusableWorker):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    def __init__(self,  ui_cg: CommandGroup, ui_wg: WindowGroup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui_cg = ui_cg
        self.ui_wg = ui_wg

    def try_send_messages(self):
        hwnds = get_selected_data(self.ui_wg.window_listbox)
        if len(hwnds) < 1:
            log(f'\nNo hwnds selected')
            return
        else:
            log(f'\nTrying to send to hwnds: {hwnds}')

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
            for hwnd in hwnds:
                run_test_message(hwnd, cw.cmd, args)
                log(f"{cw.cmd} {args}")
                # TODO QTimer
                sleep(.2)

    @Slot()
    @override
    def on_run(self):
        log(f"Next 10s sending messages to background selected window or \n"
                      f"try to switch window to test foreground send")

        def on_err(e: Exception):
            log('Safe_catch: ' + str(e))
        with context_switch(catch_exceptions(on_err), True):
            for _ in range(0, 10):
                self.try_send_messages()
                # TODO QTimer
                sleep(1)
        log(f"Send over")
