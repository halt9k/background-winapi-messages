import functools
from functools import wraps
from typing_extensions import override as typing_extensions_override


def virutalmethod(method):
    """ Decorator to hint that optional override is possible """
    method.__isvirtualmethod__ = True
    return method


def ensure_ancestor_method_labeled(method, self):
    for ancestor in self.__class__.__mro__:
        if ancestor == self.__class__:
            continue

        base_method = getattr(ancestor, method.__name__, None)
        if base_method:
            is_abstract = getattr(base_method, '__isabstractmethod__', False)
            is_virtual = getattr(base_method, '__isvirtualmethod__', False)
            # is_override = getattr(base_method, '__override__', False)
            if is_virtual or is_abstract:
                return

    module = method.__module__
    qualname = method.__qualname__
    print(f"\n WARNING: {module}.{qualname} has no inheritance decorator \n")


def override(method):
    """
    Optional, just verifies inheritance decorators.
    Not an optimal way to check and will be replaced later.
    """

    @wraps(method)
    @typing_extensions_override
    def method_with_override(self, *args, **kwargs):
        if not hasattr(method, "__override_check_done__"):
            ensure_ancestor_method_labeled(method, self)
            method.__override_check_done__ = True
        return method(self, *args, **kwargs)

    return method_with_override
