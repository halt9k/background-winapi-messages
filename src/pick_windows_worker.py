from time import sleep

import win32gui
from PySide6.QtCore import Signal, Slot, QTimer, QThread

from src.helpers.python_extensions import catch_exceptions, ChangeTracker, context_switch
from src.helpers.qt import log, QTimerEx
from src.helpers.qt_async_button import QWorker
from src.helpers.virtual_methods import override
from src.helpers.winapi.other import MouseTracker, get_window_info_under_cursor


class PickWindowsWorker(QWorker):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    pick_hwnd = Signal(int)

    def __init__(self):
        super(PickWindowsWorker, self).__init__()
        self.cursor_wnd_tracker = None
        self.focused_wnd_tracker = None
        self.check_timer = None
        self.finished.connect(self.on_finished)

    def check_window_under_cursor(self) -> bool:
        changed, (hwnd, title) = self.cursor_wnd_tracker.track()

        if changed:
            log(f'Hwnd: {hwnd}, title: {title}')

        changed_focus, _ = self.focused_wnd_tracker.track()
        if changed_focus:
            self.pick_hwnd.emit(hwnd)
            return False
        return True

    def on_check_timer(self):
        # it's also possible to skip QTimer with QThread.sleep(), which is SendMessagesWorker case nearby
        # but event based here is an solid alternative
        def on_err(e: Exception):
            log('Safe_catch: ' + str(e))

        with context_switch(catch_exceptions(on_err), False):
            if not self.check_window_under_cursor():
                del self.check_timer
                self.finished.emit()

    @Slot()
    @override
    def on_run(self):
        log("\n"
            "Move cursor around next 10s and check log.\n"
            "Change focus (click) to select hwnd in the list.\n")

        self.cursor_wnd_tracker = ChangeTracker(get_window_info_under_cursor)
        self.focused_wnd_tracker = ChangeTracker(win32gui.GetForegroundWindow)

        self.check_timer = QTimerEx(on_timeout=self.on_check_timer,
                                    on_finished=lambda: self.finished.emit(),
                                    repeats=100, interval_msec=100)
        self.check_timer.start()

    @Slot()
    def on_finished(self):
        log('Pick over')
