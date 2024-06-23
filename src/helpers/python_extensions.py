import inspect
import threading
from contextlib import contextmanager, nullcontext
from typing import Tuple, Any, Type, List, Callable
import fnmatch


def context_switch(context, enabled):
    return context if enabled else nullcontext()


@contextmanager
def catch_exceptions(on_catch: Callable[[Exception], None] = None):
    try:
        yield
    except Exception as e:
        if on_catch:
            on_catch(e)


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


def get_named_consts(py_module, mask: str, of_type: Type, place_on_top: [], exclude: [str] = None) \
        -> List[Tuple[str, int]]:
    members = [m for m in inspect.getmembers(py_module) if type(m[1]) == of_type]

    if not exclude:
        exclude = []
    members = [m for m in members if fnmatch.fnmatch(m[0], mask) and m[0] not in exclude]

    members.sort(key=lambda m: m[1] in place_on_top, reverse=True)
    return members
