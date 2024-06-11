#!/usr/bin/env python3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union

from win32api import CloseHandle, OpenProcess, GetWindowLong
from win32con import PROCESS_ALL_ACCESS, GWL_STYLE, WS_VISIBLE
from win32gui import GetWindowText, EnumWindows, EnumChildWindows
from win32process import GetModuleFileNameEx, GetWindowThreadProcessId


def get_unprotected_module_path(pid):
    try:
        proc = OpenProcess(PROCESS_ALL_ACCESS, 0, pid)
    except:
        # print("Process {0:d} couldn't be opened: {1:}".format(pid, traceback.format_exc()))
        return None

    try:
        return GetModuleFileNameEx(proc, None)
    except:
        # print("Error getting process name: {0:}".format(traceback.format_exc()))
        return None
    finally:
        CloseHandle(proc)


@dataclass(init=True)
class WindowInfo:
    hwnd: int
    parent_hwnd: int
    pid: int
    module_path: str
    style: int
    visible: bool
    title: str


@dataclass(init=True)
class Data:
    wnds: List[WindowInfo]
    known_parent_hwnd: Optional[int]


def on_enum_window(hwnd, data: Data):
    parent = data.known_parent_hwnd
    pid = GetWindowThreadProcessId(hwnd)[1]
    module_path = get_unprotected_module_path(pid) if pid else None
    title = GetWindowText(hwnd)
    style = GetWindowLong(hwnd, GWL_STYLE)
    visible = bool(WS_VISIBLE & style)

    data.wnds += [WindowInfo(hwnd, parent, pid, module_path, style, visible, title)]
    return True


def filter_process_windows(data: List[WindowInfo],
                           pid: int = None,
                           module_exe: str = None,
                           remove_invisible=True) -> List[WindowInfo]:
    filtered = []
    for wnd in data:
        if pid and wnd.pid != pid:
            continue
        if module_exe and (wnd.module_path is None or module_exe.lower() not in wnd.module_path.lower()):
            continue
        if remove_invisible and not wnd.visible:
            continue
        filtered += [wnd]

    before, after = len(data), len(filtered)
    if before > after:
        print(f'get_process_windows filter: {before} to {after}')

    return filtered


def get_process_windows() -> List[WindowInfo]:
    data = Data([], None)
    EnumWindows(on_enum_window, data)
    for wnd in data.wnds:
        data.known_parent_hwnd = wnd.hwnd
        EnumChildWindows(wnd.hwnd, on_enum_window, data)
    data.wnds.sort(key=lambda wnd: wnd.pid)
    return data.wnds
