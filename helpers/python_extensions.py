import threading
from contextlib import contextmanager
from typing import Tuple


def run_in_thread(func, *args, **kwargs):
    result = None

    def thread_target():
        nonlocal result
        result = func(*args, **kwargs)

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    return result
