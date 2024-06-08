import threading
from contextlib import contextmanager
from typing import Tuple, Any


@contextmanager
def safe_catch():
    try:
        yield
    except Exception as e:
        print('Safe_catch: ' + str(e))


def run_in_thread(func, *args, **kwargs):
    result = None

    def thread_target():
        nonlocal result
        result = func(*args, **kwargs)

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    return result


class ChangeTracker:
    def __init__(self, func):
        self.func = func
        self.prev_value = func()

    def track(self) -> Tuple[bool, Any]:
        cur_value = self.func()
        changed = cur_value != self.prev_value
        self.prev_value = cur_value

        return changed, cur_value
