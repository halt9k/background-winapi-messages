import contextlib
from abc import abstractmethod

import pydevd
from PySide6.QtCore import Qt, Signal, QObject, QTimer, Slot, QTimerEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QListWidget, QComboBox

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


class QDebuggedTimer(QTimer):
    """ Warning: any slot connected to timeout signal won't be breakpointed """

    def timerEvent(self, arg__1: QTimerEvent) -> None:
        pydevd.settrace(suspend=False)
        self.on_timeout()

    @abstractmethod
    def on_timeout(self):
        raise NotImplementedError


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


class QTimerEx(QDebuggedTimer):
    def __init__(self, on_timeout, on_finished, repeats=3, interval_msec=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setInterval(interval_msec)
        self.count = 0
        self.target_count = repeats
        self.on_timeout_user = on_timeout
        self.on_finished = on_finished

    @Slot()
    def on_timeout(self):
        if self.count >= self.target_count:
            self.stop()
            self.on_finished()
            return
        self.on_timeout_user()
        self.count += 1

