import threading
from contextlib import contextmanager, nullcontext
from typing import Tuple, Any


def context_switch(context, enabled):
    return context if enabled else nullcontext()


@contextmanager
def catch_exceptions(func=None):
    try:
        yield
    except Exception as e:
        if func:
            func(e)


def run_in_thread(func, *args, **kwargs):
    # result = None

    def thread_target():
        # nonlocal result
        # result = func(*args, **kwargs)
        func(*args, **kwargs)

    thread = threading.Thread(target=thread_target)
    thread.start()
    # thread.join()
    # return result


class ChangeTracker:
    """ Useful to track and respond to a change in some function return values """

    def __init__(self, tracked_func):
        self.func = tracked_func
        self.prev_value = tracked_func()

    def track(self) -> Tuple[bool, Any]:
        """ Returns if changed and function value """

        cur_value = self.func()
        changed = cur_value != self.prev_value
        self.prev_value = cur_value

        return changed, cur_value
