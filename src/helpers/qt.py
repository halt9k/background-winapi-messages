import contextlib
from abc import abstractmethod
from typing import Callable

from PySide6.QtCore import Qt, QThread, Signal, Slot, QObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QAbstractButton, QListWidget, QPushButton
import pydevd

from src.helpers.virtual_methods import virutalmethod, override
from src.helpers.python_extensions import context_switch


class Logger(QObject):
    log = Signal(str)


logger = Logger()
log = logger.log.emit


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


class QWorker(QObject):
    finished = Signal()

    @abstractmethod
    def on_run(self):
        raise NotImplementedError

    @Slot()
    def run(self):
        pydevd.settrace(suspend=False)
        try:
            self.on_run()
        finally:
            self.finished.emit()


class QAsyncButton(QPushButton):
    def __init__(self, contexts=None,
                 on_before_thread: Callable = None,
                 on_after_thread: Callable = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contexts = []
        # self.contexts = contexts
        self.on_custom_before_thread = on_before_thread
        self.on_custom_after_thread = on_after_thread

        self.thread = QThread()
        self.clicked.connect(self.on_clicked)
        self.worker = None

    def on_before_thread(self):
        # TODO fixed?
        # Some contexts which wrap a thread must be executed
        # before thread start and after thread finish
        # wrapping this in context managers  is desired, but they won't wait until finish
        # declaring separate slots is solid, but too code cluttering
        # using manual contexts like here is clean, but yet skips error handling

        self.setEnabled(False)
        self.enter_contexts()
        if self.on_custom_before_thread:
            self.on_custom_before_thread()

    @Slot()
    def on_after_thread(self):
        if self.on_custom_after_thread:
            self.on_custom_after_thread()
        self.setEnabled(True)
        self.exit_contexts()

    @Slot()
    def on_clicked(self) -> None:
        # TODO contexts?
        assert self.worker

        self.on_before_thread()
        self.thread.finished.connect(self.on_after_thread)

        self.thread.start()

    def attach_worker(self, worker: QWorker):
        self.worker = worker
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)

    def exit_contexts(self):
        for c in reversed(self.contexts):
            # TODO propagate errors?
            c.__exit__(None, None, None)

    def enter_contexts(self):
        for c in self.contexts:
            c.__enter__()
