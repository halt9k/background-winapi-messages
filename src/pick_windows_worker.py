from typing import Optional

import win32gui
from PySide6.QtCore import Signal, Slot

from src.helpers.python_extensions import catch_exceptions, ChangeTracker, context_switch
from src.helpers.qt import Logger, QNTimer, qntimer_timeout_slot
from src.helpers.qt_async_button import QWorker
from src.helpers.virtual_methods import override
from src.helpers.winapi.other import get_window_info_under_cursor


class PickWindowsWorker(QWorker):
    # non threaded QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    pick_hwnd = Signal(int)

    def __init__(self):
        super(PickWindowsWorker, self).__init__()
        self.cursor_wnd_tracker = None
        self.focused_wnd_tracker = None

        # TODO if worker later moved to thread, timer is not ?!
        self.check_timer: Optional[QNTimer] = None

    def check_window_under_cursor(self) -> bool:
        changed, (hwnd, title) = self.cursor_wnd_tracker.track()

        if changed:
            Logger.log(f'Hwnd: {hwnd}, title: {title}')

        changed_focus, _ = self.focused_wnd_tracker.track()
        if changed_focus:
            self.pick_hwnd.emit(hwnd)
            return False
        return True

    @qntimer_timeout_slot
    def on_check_timer(self, n):
        # it was also possible to skip QTimer and threads
        # but event based approach makes a proper experimental sandbox for future tests
        if not self.check_window_under_cursor():
            self.check_timer.stop()
            self.finished.emit()

    @Slot()
    @override
    def on_run(self):
        Logger.log("\n"
                   "Move cursor around next 10s and check log.\n"
                   "Change focus (click) to select hwnd in the list.\n")

        self.cursor_wnd_tracker = ChangeTracker(get_window_info_under_cursor)
        self.focused_wnd_tracker = ChangeTracker(win32gui.GetForegroundWindow)

        self.check_timer = QNTimer(stop_on_emit=True)
        self.check_timer.timeout_n.connect(self.on_check_timer)
        self.check_timer.finished.connect(self.finished)
        self.check_timer.start(repeats=100, interval_msec=100)

    @Slot()
    @override
    def on_finished(self):
        Logger.log('Pick over')
