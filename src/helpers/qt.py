import contextlib
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QAbstractButton
import pydevd

from src.helpers.virtual_methods import virutalmethod
from src.helpers.python_extensions import context_switch


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


class QContextedThread(QThread):
    # Some contexts which wrap a thread must be executed
    # before thread start and after thread finish
    # wrapping this in context managers  is desired, but they won't wait until finish
    # declaring separate slots is solid, but too code cluttering
    # using manual contexts like here is clean, but yet skips error handling
    # TODO is moveToThread approach any different in context of this problem?
    log = Signal(str)

    def __init__(self, on_log: Slot(str), contexts: [], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.connect(on_log)
        self.contexts = contexts

        self.enter_contexts()
        self.finished.connect(self.exit_contexts)

    def enter_contexts(self):
        for c in self.contexts:
            c.__enter__()

    @virutalmethod
    def run(self):
        # without this debug won't hit breakpoints in the threads
        pydevd.settrace(suspend=False)

    @Slot()
    def exit_contexts(self):
        for c in reversed(self.contexts):
            # TODO propagate errors?
            c.__exit__(None, None, None)


class QButtonThread(QContextedThread):
    def __init__(self, btn: QAbstractButton, on_log: Slot(str), *args, **kwargs):
        # Reminder: __init__ runs not yet in thread

        super().__init__(on_log, *args, **kwargs)
        btn.setEnabled(False)
        self.finished.connect(lambda: btn.setEnabled(True))


