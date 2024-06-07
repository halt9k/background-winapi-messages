import contextlib
from typing import Type, Union, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QApplication, QMainWindow, QListWidget, QListWidgetItem


@contextlib.contextmanager
def keep_window_visible(wnd: Type[QWidget]):
    visible = wnd.isVisible()
    yield
    if visible != wnd.isVisible():
        wnd.setVisible(visible)


@contextlib.contextmanager
def switch_window_flag(wnd: Union[Type[QWidget], Any], flag: Qt.WindowType, value, visible=True):
    bkp = flag in wnd.windowFlags()
    visible = wnd.isVisible()
    with keep_window_visible(wnd):
        wnd.setWindowFlag(flag, value)
    yield
    with keep_window_visible(wnd):
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