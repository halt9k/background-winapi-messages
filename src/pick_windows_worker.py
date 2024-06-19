from time import sleep

import win32gui
from PySide6.QtCore import Signal, Slot

from src.helpers.python_extensions import catch_exceptions, ChangeTracker, context_switch
from src.helpers.qt import log
from src.helpers.qt_async_button import QReusableWorker
from src.helpers.virtual_methods import override
from src.helpers.winapi.other import MouseTracker, get_window_info_under_cursor


class PickWindowsWorker(QReusableWorker):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    pick_hwnd = Signal(int)

    def check_window_under_cursor(self, cursor_wnd, focused_wnd: ChangeTracker) -> bool:
        changed, (hwnd, title) = cursor_wnd.track()

        if changed:
            log(f'Hwnd: {hwnd}, title: {title}')

        if focused_wnd.track()[0]:
            self.pick_hwnd.emit(hwnd)
            return False
        return True

    @Slot()
    @override
    def on_run(self):
        log("\n"
            "Move cursor around next 10s and check log.\n"
            "Change focus (click) to select hwnd in the list.\n")

        def on_err(e: Exception):
            log('Safe_catch: ' + str(e))

        with context_switch(catch_exceptions(on_err), False):
            # mouse_tracker = MouseTracker()
            cursor_wnd_tracker = ChangeTracker(get_window_info_under_cursor)
            focused_wnd_tracker = ChangeTracker(win32gui.GetForegroundWindow)

            for _ in range(0, 100):
                if not self.check_window_under_cursor(cursor_wnd_tracker, focused_wnd_tracker):
                    break
                sleep(0.100)

        log('Pick over')
