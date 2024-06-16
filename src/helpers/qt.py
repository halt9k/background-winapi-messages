import contextlib

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QListWidget

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


