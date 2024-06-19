from dataclasses import dataclass
from typing import List, Tuple

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


message_presets = ((mouse_events.send_click,),
                   (keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
                   (PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'a'),
                   (PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'a'),
                   (keybd_event, 'VK_LCONTROL', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP)),
                   (SendMessage, EnumArg(wm_args, win32con.WM_CHAR), 'b'),
                   (PostMessage, EnumArg(wm_args, win32con.WM_KEYDOWN), 'c'),
                   (PostMessage, EnumArg(wm_args, win32con.WM_KEYUP), 'c'),
                   (PostMessage, EnumArg(wm_args, win32con.WM_CHAR), 'd'),
                   (keybd_event, 'e', EnumArg(keyevent_args, KEYEVENTF_KEYDOWN)),
                   (keybd_event, 'e', EnumArg(keyevent_args, win32con.KEYEVENTF_KEYUP)))


@dataclass(init=True)
class UiArgs:
    # this may not fit all the use future cmd cases, but currently is fine
    enum_arg: int = None
    key: str = None

    def key_code(self):
        assert self.key
        if len(self.key) == 1:
            # 'a', '1'
            return virtual_code(self.key)
        elif self.key.isnumeric():
            # '143'
            key_code = int(self.key)
            return int(self.key)
        else:
            # 'VK_TAB'
            found_key = [arg for arg in vk_args if arg[0] == self.key]
            assert len(found_key) > 0
            return found_key[0][1]


def run_test_message(hwnd, cmd, ui_args: UiArgs):
    # cmd also can have any custom user function like mouse_events.send_click

    if cmd == mouse_events.send_click:
        l, t, r, b = GetWindowRect(hwnd)
        cx, cy = GetCursorPos()
        # relative to window corner if top-level hwnd
        rx, ry = cx - l, cy - t
        mouse_events.send_click(hwnd, rx, ry)

    elif cmd == SendMessage:
        SendMessage(hwnd, ui_args.enum_arg, ui_args.key_code(), 0)

    elif cmd == PostMessage:
        PostMessage(hwnd, ui_args.enum_arg, ui_args.key_code(), 0)

    elif cmd == keybd_event:
        keybd_event(ui_args.key_code(), 0, ui_args.enum_arg, 0)

    else:
        raise NotImplementedError
