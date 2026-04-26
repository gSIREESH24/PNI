from .function_registry import FunctionRegistry
from . import stub_runner


class Dispatcher:

    def __init__(self, registry: FunctionRegistry):
        self._registry = registry

    def call(self, name: str, *args, context=None):
        entry = self._registry.get_function(name)
        if entry is None:
            raise NameError(f"[Bridge] Function '{name}' is not registered.")

        if entry.func is not None:
            return entry.func(*args)

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
