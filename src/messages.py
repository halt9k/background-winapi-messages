from dataclasses import dataclass
from typing import List, Tuple, Callable

import win32con
from win32api import SendMessage, PostMessage, keybd_event
from win32gui import GetWindowRect, GetCursorPos

import src.helpers.winapi.mouse_events as mouse_events
from src.helpers.python_extensions import get_named_consts
from src.helpers.winapi.hotkey_events import virtual_code

common_vks = [win32con.VK_LSHIFT, win32con.VK_LCONTROL, win32con.VK_LMENU, win32con.VK_RETURN, win32con.VK_TAB]
vk_args = get_named_consts(win32con, 'VK_*', int, common_vks)

common_wms = [win32con.WM_KEYDOWN, win32con.WM_CHAR, win32con.WM_KEYUP]
wm_args = get_named_consts(win32con, 'WM_*', int, common_wms, exclude=['WM_KEYFIRST'])

KEYEVENTF_KEYDOWN = 0
common_keyevents = get_named_consts(win32con, 'KEYEVENTF_*', int, [win32con.KEYEVENTF_KEYUP])
keyevent_args = [('KEYEVENTF_KEYDOWN', KEYEVENTF_KEYDOWN)] + common_keyevents


@dataclass(init=True)
class EnumArg:
    named_values: List[Tuple[str, int]]
    value: int


@dataclass
class WinMsg:
    def __init__(self, cmd, *args):
        self.cmd = cmd
        for arg in args:
            if type(arg) is str:
                self.str_arg1 = arg
            if type(arg) is EnumArg:
                self.enum_arg1 = arg

    cmd: Callable
    enum_arg1: EnumArg = None
    str_arg1: str = None


message_presets: List[WinMsg] = [
    # not packing commands even futher to keep debug transparent, arg order is kept for clarity

    WinMsg(mouse_events.send_click),
    WinMsg(keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'a'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'a'),
    WinMsg(keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP)),
    WinMsg(SendMessage, EnumArg(wm_args, win32con.WM_CHAR), 'b'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'c'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'c'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_CHAR), 'd'),
    WinMsg(keybd_event, 'e', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
    WinMsg(keybd_event, 'e', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP))
]


def key_code(key: str):
    if len(key) == 1:
        # 'a', '1'
        return virtual_code(key)
    elif key.isnumeric():
        # '143'
        return int(key)
    else:
        # 'VK_TAB'
        found_key = [arg for arg in vk_args if arg[0] == key]
        assert len(found_key) > 0
        return found_key[0][1]


def run_test_message(hwnd, win_msg: WinMsg):
    # cmd also can have any custom user function like mouse_events.send_click

    key = key_code(win_msg.str_arg1) if win_msg.str_arg1 else None
    enum_arg_value = win_msg.enum_arg1.value if win_msg.enum_arg1 else None

    if win_msg.cmd == mouse_events.send_click:
        l, t, r, b = GetWindowRect(hwnd)
        cx, cy = GetCursorPos()
        # relative to window corner if top-level hwnd
        rx, ry = cx - l, cy - t
        mouse_events.send_click(hwnd, rx, ry)

    elif win_msg.cmd == SendMessage:
        SendMessage(hwnd, enum_arg_value, key, 0)

    elif win_msg.cmd == PostMessage:
        PostMessage(hwnd, enum_arg_value, key, 0)

    elif win_msg.cmd == keybd_event:
        keybd_event(key, 0, enum_arg_value, 0)

    else:
        raise NotImplementedError
