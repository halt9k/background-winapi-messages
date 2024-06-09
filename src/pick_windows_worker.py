from PySide6.QtCore import QThread, Signal, Slot

from src.helpers.python_extensions import catch_exceptions, ChangeTracker, context_switch
from src.helpers.qt import QButtonThread
from src.helpers.winapi.other import MouseTracker, get_window_info_under_cursor


class PickWindowsThread(QButtonThread):
    # QTimer is better option for this specific task,
    # but thread template may be handy for future extensions,
    # since this is also sandbox for Qt hwnd experiments

    pick_hwnd = Signal(int)

    def __init__(self, on_pick_hwnd: Slot(int), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pick_hwnd.connect(on_pick_hwnd)

    def check_window_under_cursor(self, mouse_tracker: MouseTracker, window_tracker: ChangeTracker) -> bool:
        changed, (hwnd, title) = window_tracker.track()

        if changed:
            self.log.emit(f'Hwnd: {hwnd}, title: {title}')

        if mouse_tracker.track(10) > 3:
            self.pick_hwnd.emit(hwnd)
            return False

        self.msleep(100)
        return True

    def run(self):
        self.log.emit("\n"
                      "Move cursor around next 10 sec and check log.\n"
                      "Idle 3s to auto select hwnd in the list.\n")

        def on_err(e: Exception):
            self.log.emit('Safe_catch: ' + str(e))

        with context_switch(catch_exceptions(on_err), True):
            mouse_tracker = MouseTracker()
            title_tracker = ChangeTracker(get_window_info_under_cursor)

            for _ in range(0, 100):
                if not self.check_window_under_cursor(mouse_tracker, title_tracker):
                    break

        self.log.emit('Pick over')
