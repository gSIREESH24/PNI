"""
dispatcher.py — Routes bridge function calls to their implementations.

Two execution paths:
  1. Python-owned function  → called directly via entry.func(*args).
  2. Subprocess stub        → re-launched through stub_runner.invoke().
"""

from .function_registry import FunctionRegistry
from . import stub_runner


class Dispatcher:
    """
    Given a function name and arguments, finds the right implementation
    and invokes it — whether that's a Python callable or a native stub.
    """

    def __init__(self, registry: FunctionRegistry):
        self._registry = registry

    def call(self, name: str, *args, context=None):
        entry = self._registry.get_function(name)
        if entry is None:
            raise NameError(f"[Bridge] Function '{name}' is not registered.")

        # Python-owned: call directly.
        if entry.func is not None:
            return entry.func(*args)

        # Subprocess stub: re-invoke through stub_runner.
        if entry.stub_source is not None:
            return stub_runner.invoke(
                fn_name     = entry.name,
                language    = entry.language,
                source      = entry.stub_source,
                return_type = entry.return_type or "int",
                args        = list(args),
                context     = context,
            )

        raise RuntimeError(
            f"[Bridge] Function '{name}' (language='{entry.language}') "
            f"has no callable and no stub source."
        )

    def has_callable(self, name: str) -> bool:
        entry = self._registry.get_function(name)
        return entry is not None and (callable(entry.func) or entry.stub_source is not None)
