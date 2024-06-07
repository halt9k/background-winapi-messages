from contextlib import contextmanager
from enum import Enum
from time import sleep

import win32con
import win32gui
import pyautogui

from helpers.winapi.processes import get_process_windows, filter_process_windows


class MissingWindowFocusException(Exception):
    pass


class WindowState(Enum):
    MAX = win32con.SW_SHOWMAXIMIZED
    MIN = win32con.SW_SHOWMINIMIZED
    NORM = win32con.SW_SHOWNORMAL


def get_dims(hwnd):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bottom - top
    return w, h


def verboose_sleep(sec):
    print(f"Sleep {sec}")
    sleep(sec)


@contextmanager
def hwnd_unsafe_op(post_delay, hwnd, require_focus=False, keep_state=False):
    # reminder: during sleep windows can be closed, moved, trayed, switched

    if require_focus and win32gui.GetForegroundWindow() != hwnd:
        raise MissingWindowFocusException(f'Window inactive unexpectedly: {hwnd}')

    if is_window_closed(hwnd):
        raise Exception(f'Window closed unexpectedly: {hwnd}')

    yield

    if post_delay < 0:
        state = get_window_state(hwnd) if keep_state else None
        verboose_sleep(post_delay)
        if keep_state and state != get_window_state(hwnd):
            raise Exception(f'Window changed state while sleep: {hwnd}')

        if require_focus and win32gui.GetForegroundWindow() != hwnd:
            raise MissingWindowFocusException(f'Window went inactive while sleep: {hwnd}')


@contextmanager
def switch_focus_window(hwnd, delay=0.1):
    prev_hwnd = win32gui.GetForegroundWindow()

    if prev_hwnd != hwnd:
        pyautogui.press("alt")
        win32gui.SetForegroundWindow(hwnd)
        verboose_sleep(delay)

    if win32gui.GetForegroundWindow() == hwnd:
        yield
        if prev_hwnd != hwnd:
            win32gui.SetForegroundWindow(prev_hwnd)
            verboose_sleep(delay)
    else:
        raise MissingWindowFocusException(f'Window activation failed: {hwnd}')


def safe_call(func, return_on_error):
    # Most of hwnd related funcs are async and unreliable
    try:
        return func()
    except Exception as e:
        print(f"Expected exception caught by safety guard: ")
        print(e)
        return return_on_error


def get_window_state(hwnd) -> WindowState:
    place = win32gui.GetWindowPlacement(hwnd)
    state = WindowState(place[1])
    return state


def get_title(hwnd):
    return win32gui.GetWindowText(hwnd)


def set_title(hwnd, title):
    """ Be aware that Chrome userscript cannot read this though """
    win32gui.SetWindowText(hwnd, title)


def is_window_closed(hwnd):
    return not win32gui.IsWindow(hwnd)


def is_any_window_maxed(module=None) -> bool:
    # hwnd = win32gui.GetForegroundWindow()

    wnds = get_process_windows()
    visible = filter_process_windows(wnds, module_exe=module)
    maxed: bool = any([get_window_state(wnd.hwnd) == WindowState.MAX for wnd in visible])

    return maxed
