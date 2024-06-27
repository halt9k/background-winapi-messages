import contextlib
import functools
from abc import abstractmethod

import pydevd
from PySide6.QtCore import Qt, Signal, QObject, QTimer, Slot, QTimerEvent, QThread, QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QListWidget, QComboBox
from typing_extensions import override

from src.helpers.python_extensions import context_switch


class Logger(QObject):
    log_signal = Signal(str)

    instance = None

    def __init__(self):
        super().__init__()
        assert not Logger.instance
        Logger.instance = self

    @staticmethod
    def log_err(e: Exception):
        Logger.instance.log_signal.emit(str(e))

    @staticmethod
    def log(msg):
        Logger.instance.log_signal.emit(msg)


Logger()


@contextlib.contextmanager
def keep_window_visible(wnd: QWidget):
    visible = wnd.isVisible()
    yield
    if visible != wnd.isVisible():
        wnd.setVisible(visible)


@contextlib.contextmanager
def switch_window_flag(wnd: QWidget, flag: Qt.WindowType, value, keep_visible=True):
    bkp = flag in wnd.windowFlags()
    with context_switch(keep_window_visible(wnd), keep_visible):
        wnd.setWindowFlag(flag, value)
    yield
    with context_switch(keep_window_visible(wnd), keep_visible):
        wnd.setWindowFlag(flag, bkp)


class QListWidgetItemEx(QListWidgetItem):
    def __init__(self, key: int, text, font_bold=False, font_red=False):
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, key)
        if font_bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        if font_red:
            self.setForeground(QColor("red"))


def find_by_item_data(lw: QListWidget, data):
    items = [lw.item(x) for x in range(lw.count())]
    found = [i for i in items if i.data(Qt.ItemDataRole.UserRole) == data]
    return found


def get_selected_data(lw: QListWidget):
    selected_items = lw.selectedItems()
    return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]


class QTracedThread(QThread):
    # TODO post on stack, must have both in thread and worker?
    @override
    def run(self):
        # without this, breakpoints may not work under IDE
        pydevd.settrace(suspend=False)
        super(QTracedThread, self).run()


class QComboBoxEx(QComboBox):
    def __init__(self, parent, values, default_value, min_content_length=5):
        super().__init__(parent)
        cur_index = None
        for i, (key, value) in enumerate(values):
            self.addItem(key, value)
            if value == default_value:
                cur_index = i
        if cur_index:
            self.setCurrentIndex(cur_index)

        if min_content_length:
            self.setMinimumContentsLength(min_content_length)
            self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)


class QNTimer(QTimer):
    """
    This ~async QNTimer is intended to reaplce a standard sequential for loop.

    # started.emit()
    for n in range (0, repeats)
       timeout_n.emit(self, n)
       # waits for self.continue_loops()
    finished.emit()

    There are multile ways to implement loop timer:
        can be done via 1 or 2, QNTimer uses _1_:
        _1_) overriding timeout with new signal timeout_py
        2) replacing signals completely with callbacks
    There are multile ways to have finished() call either, QNTimer uses _1_:
        _1_) only if expected amount of loops passed, stopping timer on each loop until started exernally
        2) call loops and finished async no matter what, just when time reached
        3) same async as 2, but possibly stopiing or repeating if previous step fails
    """
    finished = Signal()
    timeout_n = Signal(QTimer, int)

    def __init__(self, stop_on_emit=True,  *args, **kwargs):
        """
        Parameters:
        stop_on_emit:
            - False: QNTimer simply firing all events and than finish no matter what
            - True: QNTimer expects continue_steps Slot after each timeout and finish won't happen without continue
        """
        super().__init__(*args, **kwargs)

        self.count = None
        self.target_count = None
        self.stop_on_emit = stop_on_emit

        super().timeout.connect(self.on_timeout)
        self.timeout = None

    @Slot()
    def on_timeout(self):
        self.count += 1
        if self.count > self.target_count:
            self.quit()

        if self.stop_on_emit:
            self.stop()

        self.timeout_n.emit(self, self.count)

    @override
    def start(self, repeats, interval_msec):
        self.count = 0
        self.target_count = repeats
        self.setInterval(interval_msec)
        super().start()

    @Slot()
    def continue_loops(self):
        assert self.count > 0
        super().start()

    def quit(self):
        self.stop()
        self.finished.emit()


def qntimer_timeout_slot(method):
    """
    Good wrapper for simple on_ntimer routines,
    but finally may be async if a chain of Qt events is expected
    """

    @functools.wraps(method)
    def wrapper(obj, timer: QNTimer, step_n: int, *args, **kwargs):
        try:
            method(obj, step_n, *args,  **kwargs)
        except:
            timer.quit()
            raise
        finally:
            # TODO Slot or callback?
            timer.continue_loops()
    return wrapper
