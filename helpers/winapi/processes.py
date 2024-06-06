#!/usr/bin/env python3
import contextlib
import os
from pathlib import Path

import win32api as wapi
import win32con as wcon
import win32gui as wgui
import win32process as wproc


def enum_windows_proc(hwnd, param):
    """ Callback for Winapi  """

    pid = param.get("pid", None)
    data = param.get("data", None)

    if pid and wproc.GetWindowThreadProcessId(hwnd)[1] != pid:
        return True

    text = wgui.GetWindowText(hwnd)
    if not text:
        return True

    style = wapi.GetWindowLong(hwnd, wcon.GWL_STYLE)
    if style & wcon.WS_VISIBLE:
        if data is not None:
            data.append((hwnd, text))
        else:
            print("enum_windows_proc: %08X - %s" % (hwnd, text))
    return True


def get_process_windows(pid=None):
    data = []
    param = {
        "pid": pid,
        "data": data,
    }
    wgui.EnumWindows(enum_windows_proc, param)
    return data


def try_get_exe_path(pid):
    try:
        proc = wapi.OpenProcess(wcon.PROCESS_ALL_ACCESS, 0, pid)
    except:
        # print("Process {0:d} couldn't be opened: {1:}".format(pid, traceback.format_exc()))
        return None

    try:
        return wproc.GetModuleFileNameEx(proc, None)
    except:
        # print("Error getting process name: {0:}".format(traceback.format_exc()))
        return None
    finally:
        wapi.CloseHandle(proc)


def get_module_paths(proc_filter_func=None):
    procs = wproc.EnumProcesses()
    pid_paths = [(pid, try_get_exe_path(pid)) for pid in procs]
    filtered = [(pid, Path(path).name) for pid, path in pid_paths if path]

    if proc_filter_func:
        filtered = [(pid, bname) for pid, bname in filtered if proc_filter_func(bname)]

    return filtered

