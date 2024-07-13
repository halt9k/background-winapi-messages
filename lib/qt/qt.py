from contextlib import nullcontext, contextmanager
from typing import Dict

from PySide6.QtCore import Qt, qCInfo, QLoggingCategory, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QListWidgetItem, QListWidget, QComboBox, QTextEdit, QAbstractSlider


def q_info(msg):
    qCInfo(QLoggingCategory.defaultCategory(), msg)


class QWindowUtils:
    @staticmethod
    @contextmanager
    def keep_window_visible(wnd: QWidget):
        visible = wnd.isVisible()
        yield
        if visible != wnd.isVisible():
            wnd.setVisible(visible)

    @staticmethod
    def context_switch(context, enabled):
        return context if enabled else nullcontext()

    @staticmethod
    @contextmanager
    def switch_window_flag(wnd: QWidget, flag: Qt.WindowType, value, keep_visible=True):
        bkp = flag in wnd.windowFlags()
        with QWindowUtils.context_switch(QWindowUtils.keep_window_visible(wnd), keep_visible):
            wnd.setWindowFlag(flag, value)
        yield
        with QWindowUtils.context_switch(QWindowUtils.keep_window_visible(wnd), keep_visible):
            wnd.setWindowFlag(flag, bkp)


class QListWidgetItemEx(QListWidgetItem):
    """ QListWidgetItem with data attached """
    def __init__(self, key: int, text, font_bold=False, font_red=False):
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, key)
        if font_bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        if font_red:
            self.setForeground(QColor("red"))


class QListWidgetEx(QListWidget):
    def find_by_item_data(self, data):
        items = [self.item(x) for x in range(self.count())]
        found = [i for i in items if i.data(Qt.ItemDataRole.UserRole) == data]
        return found

    def get_selected_data(self):
        selected_items = self.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]


class QComboBoxEx(QComboBox):
    """ QComboBox with dict values """
    def __init__(self, parent, values: Dict, default_value, min_content_length=5):
        """ min_content_length: limits QComboBox default width expand """
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


class QTextEditEx(QTextEdit):
    """ Keeps scroll at the bottom """

    def __init__(self, *args, **kwargs):
        super(QTextEditEx, self).__init__(*args, **kwargs)
        self.verticalScrollBar().rangeChanged.connect(self.on_range_changed)
        self.at_bottom = True

    def append(self, text):
        scrollbar = self.verticalScrollBar()
        self.at_bottom = scrollbar.value() >= (scrollbar.maximum() - 4)
        super().append(text)

    @Slot()
    def on_range_changed(self):
        if self.at_bottom:
            self.verticalScrollBar().triggerAction(QAbstractSlider.SliderAction.SliderToMaximum)

