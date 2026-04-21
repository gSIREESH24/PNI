from .registry import Registry
from . import stub_invoker


class Dispatcher:
    """
    Routes cross-language function calls through the bridge.

    Milestone 1/2: Python-owned functions — called directly via entry.func.
    Milestone 3:   Subprocess stubs       — re-invoked via stub_invoker.

    Usage:
        dispatcher.call("add", 1, 2)       # Python fn
        dispatcher.call("js_cube", 5)      # JS stub → spins up node one-shot
    """

    def __init__(self, registry: Registry):
        self._registry = registry

    def call(self, name: str, *args, context=None):
        entry = self._registry.get_function(name)

        if entry is None:
            raise NameError(
                f"[Bridge] Function '{name}' is not registered in the global registry."
            )

        # ── Python-owned: call directly ───────────────────────────────────────
        if entry.func is not None:
            return entry.func(*args)

        # ── Subprocess stub: re-invoke via stub_invoker ───────────────────────
        if entry.stub_source is not None:
            return stub_invoker.invoke(
                fn_name     = entry.name,
                language    = entry.language,
                source      = entry.stub_source,
                return_type = entry.return_type or "int",
                args        = list(args),
                context     = context,
            )

        raise RuntimeError(
            f"[Bridge] Function '{name}' is registered (language='{entry.language}') "
            f"but has no callable and no stub source. Cannot invoke."
        )

    def has_callable(self, name: str) -> bool:
        entry = self._registry.get_function(name)
        return entry is not None and (
            callable(entry.func) or entry.stub_source is not None
        )
