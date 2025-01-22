import win32gui
from PySide6.QtCore import Signal, Slot

from lib.qt.qt import q_info
from src.helpers.python_extensions import ChangeTracker
from lib.qt.qt_n_timer import QNTimer
from lib.qt.qt_async_button import QWorker
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

        self.check_timer = QNTimer(self)
        self.check_timer.timeout_n.connect(self.on_check_timer)
        self.check_timer.finished.connect(self.finished)

    def check_window_under_cursor(self) -> bool:
        changed, (hwnd, title) = self.cursor_wnd_tracker.track()

        if changed:
            q_info(f'Hwnd: {hwnd}, title: {title}')

        changed_focus, _ = self.focused_wnd_tracker.track()
        if changed_focus:
            self.pick_hwnd.emit(hwnd)
            return False
        return True

    def on_check_timer(self, n):
        # it was also possible to skip QTimer and threads
        # but event based approach makes a proper experimental sandbox for future tests
        with self.check_timer.qntimer_timeout_guard() as loop:
            if not self.check_window_under_cursor():
                self.finished.emit()
                loop.break_loop()

    @Slot()
    @override
    def on_run(self):
        q_info("\n"
               "Move cursor around next 10s and check log.\n"
               "Change focus (click) to select hwnd in the list.\n")

        self.cursor_wnd_tracker = ChangeTracker(get_window_info_under_cursor)
        self.focused_wnd_tracker = ChangeTracker(win32gui.GetForegroundWindow)

        self.check_timer.start(loop_n=100, interval_msec=100)

    @Slot()
    @override
    def on_finished(self):
        q_info('Pick over')
