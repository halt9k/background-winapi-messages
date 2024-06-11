from contextlib import contextmanager

from win32con import *
from win32api import *

from src.helpers.winapi.windows import hwnd_unsafe_op


def press_key(hwnd, key_code, only_down, post_delay_sec=0.1):
    """
    Can send standard keys, requres focus when multiple tabs opened
    key_code: can be ord('M'), ord('r'), ...
    only_down: during tests WM_KEYUP fired 2nd press, not clear why
    """

    # specifically for browsers with multiple tabs,
    # PostMessage requres focus active or it may send to the wrong tab
    with hwnd_unsafe_op(post_delay_sec, hwnd, require_focus=True, keep_state=True):
        PostMessage(hwnd, WM_KEYDOWN, key_code, 0)

    if only_down:
        return

    with hwnd_unsafe_op(post_delay_sec, hwnd, require_focus=True, keep_state=True):
        PostMessage(hwnd, WM_KEYUP, key_code, 0)


def virtual_code(char):
    assert len(char) == 1
    # Not working
    # Extract virtual-key code from the result (low byte) and apply shift state
    # shift_state = not char.islower()
    # (virtual_key_code & 0xFF) | (shift_state << 8)
    # virtual_key_code = VkKeyScan(char) & 0xFF
    return VkKeyScan(char) & 0xFF


def press_char(hwnd, char: str, only_down=True, delay_sec=0.1):
    """
    Can send a-z, A-Z, 0-9, ' '
    only_down: during tests WM_KEYUP on some sites like Google.com fired 2nd press
    """

    if 'a' < char < 'z' or '0' < char < '9' or char in [' ']:
        press_key(hwnd, virtual_code(char), only_down, delay_sec)
    elif 'A' < char < 'Z':
        with press_modifier(hwnd, VK_LSHIFT):
            press_key(hwnd, virtual_code(char), only_down, delay_sec)
    else:
        raise NotImplementedError


@contextmanager
def press_modifier(hwnd, modifier_key_code, delay_sec=0.1):
    """
    Can send Ctrl + * hotkeys, requres focus when multiple tabs opened
    modifier_key_code: usually will be win32con.VK_*, like VK_LSHIFT, VK_RSHIFT, VK_LCONTROL, VK_RCONTROL
    """

    with hwnd_unsafe_op(delay_sec, hwnd, require_focus=True, keep_state=True):
        # PostMessage not catched in combo
        keybd_event(modifier_key_code, 0, 0, 0)
    yield
    with hwnd_unsafe_op(delay_sec, hwnd, require_focus=True, keep_state=True):
        keybd_event(modifier_key_code, 0, KEYEVENTF_KEYUP, 0)

