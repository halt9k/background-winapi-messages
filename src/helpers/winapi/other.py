import math
from datetime import datetime

import win32api
from win32gui import WindowFromPoint

from src.helpers.winapi.windows import get_title


class MouseTracker:
    def __init__(self):
        self.prev_cursor = win32api.GetCursorPos()
        self.last_move = datetime.now()

    def track(self, ignore_distance_px):
        """ returns idle time based on previous calls """

        cursor = win32api.GetCursorPos()
        dist = math.dist(self.prev_cursor, cursor)
        self.prev_cursor = cursor

        if dist > ignore_distance_px:
            self.last_move = datetime.now()

        return (datetime.now() - self.last_move).total_seconds()


def get_window_info_under_cursor():
    cursor = win32api.GetCursorPos()
    hwnd = WindowFromPoint(cursor)
    title = get_title(hwnd)
    return hwnd, title
