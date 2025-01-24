from collections import OrderedDict
from typing import List, Tuple, Callable, Any, Union

import win32api
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

common_wms = [win32con.WM_KEYDOWN, win32con.WM_CHAR, win32con.WM_KEYUP]

class EnumArg:
    def __init__(self, named_values: List[Tuple[str, Any]], initial_value):
        # order is useful to have specific drop-down options on the top
        self.named_values = OrderedDict(named_values)
        self.initial_value = initial_value


class WinMsg:
    def __init__(self, cmd: Callable, *args: Union[EnumArg, str]):
        self.cmd = cmd
        self.args: List[Union[EnumArg, str]] = list(args)


message_presets: List[WinMsg] = [
    # not packing commands even futher to keep debug transparent, arg order is kept for clarity

    # TODO test
    WinMsg(mouse_events.send_click, EnumArg(mouse_events.msg_type, win32api.PostMessage)),
    WinMsg(keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'a'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'a'),
    WinMsg(keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP)),
    WinMsg(SendMessage, EnumArg(wm_args, win32con.WM_CHAR), 'b'),
    WinMsg(SendMessage, EnumArg(wm_args, win32con.WM_CHAR), '0x20'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'VK_TAB'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'VK_RETURN'),
    WinMsg(PostMessage, EnumArg(wm_args, win32con.WM_CHAR), 'd'),
    WinMsg(keybd_event, 'e', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
    WinMsg(keybd_event, 'e', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP))

]


def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False


def key_code(key: str):
    if len(key) == 1:
        # 'a', '1'
        return virtual_code(key)
    elif key.isnumeric():
        # '143'
        return int(key)
    elif is_hex(key):
        return int(key, 16)
    else:
        # 'VK_TAB'
        found_key = [arg for arg in vk_args if arg[0] == key]
        if len(found_key) == 0:
            raise RuntimeWarning(f"Code not found: {key}")
        return found_key[0][1]


def run_test_message(hwnd, win_msg: WinMsg):
    # cmd also can have any custom user function like mouse_events.send_click

    if win_msg.cmd == mouse_events.send_click:
        l, t, r, b = GetWindowRect(hwnd)
        cx, cy = GetCursorPos()
        # relative to window corner if top-level hwnd
        rx, ry = cx - l, cy - t
        enum_arg_value = win_msg.args[0].initial_value
        mouse_events.send_click(hwnd, rx, ry, enum_arg_value)

    elif win_msg.cmd == SendMessage:
        enum_arg_value = win_msg.args[0].initial_value
        key = key_code(win_msg.args[1])
        SendMessage(hwnd, enum_arg_value, key, 0)

    elif win_msg.cmd == PostMessage:
        enum_arg_value = win_msg.args[0].initial_value
        key = key_code(win_msg.args[1])
        PostMessage(hwnd, enum_arg_value, key, 0)

    elif win_msg.cmd == keybd_event:
        key = key_code(win_msg.args[0])
        enum_arg_value = win_msg.args[1].initial_value
        keybd_event(key, 0, enum_arg_value, 0)

    else:
        raise NotImplementedError
