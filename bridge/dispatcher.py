from .registry import Registry


class Dispatcher:
    """
    Routes cross-language function calls through the bridge.

    Phase-2 supports direct calls only for Python-owned functions
    (because they live in-process). Subprocess languages (JS, C, C++, Java)
    cannot be called back at runtime — that is a Phase-3 concern.

    Usage:
        dispatcher.call("add", 1, 2)   # returns result of registered function
    """

    def __init__(self, registry: Registry):
        self._registry = registry

    def call(self, name: str, *args):
        entry = self._registry.get_function(name)

        if entry is None:
            raise NameError(
                f"[Bridge] Function '{name}' is not registered in the global registry."
            )

        if entry.func is None:
            raise RuntimeError(
                f"[Bridge] Function '{name}' is owned by '{entry.language}' "
                f"(subprocess language) and cannot be called back in Phase-2."
            )

        return entry.func(*args)

    def has_callable(self, name: str) -> bool:
        entry = self._registry.get_function(name)
        return entry is not None and callable(entry.func)
