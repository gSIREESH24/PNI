"""
bridge.py — Central PLF bridge: the single object all language adapters talk through.

Owns three subsystems:
  registry   : stores all shared values, functions, and class schemas
  store      : handle-based storage for non-primitive Python objects
  dispatcher : routes call(name, args) to Python callables or native stubs

Design rule: no language ever talks directly to another language.
Every value and every call passes through this bridge.
"""

from .function_registry import FunctionRegistry
from .object_store      import ObjectStore
from .dispatcher        import Dispatcher


class Bridge:
    """The central runtime hub of the Polyglot Language Framework."""

    def __init__(self):
        self.registry   = FunctionRegistry()
        self.store      = ObjectStore()
        self.dispatcher = Dispatcher(self.registry)

    # ── Shared scalar values ──────────────────────────────────────────────────

    def set(self, name: str, value):
        """Publish a value so all subsequent language blocks can read it."""
        self.registry.set_value(name, value)

    def get(self, name: str, default=None):
        """Read a previously published value."""
        return self.registry.get_value(name, default)

    def all_values(self) -> dict:
        """Snapshot of every current shared value."""
        return dict(self.registry.values)

    # ── Functions ─────────────────────────────────────────────────────────────

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type: str = None):
        """Register a Python callable so native languages can call it."""
        self.registry.register_python_function(name, func, param_types, return_type)

    def register_class_schema(self, name: str, fields: dict[str, str]):
        """Register a class layout for cross-language struct/class generation."""
        self.registry.register_class_schema(name, fields)

    def register_stub(self, name: str, language: str, source: str,
                      return_type: str = "int"):
        """Register a native-language function stub for Python-side calling."""
        self.registry.register_stub(name, language, source, return_type)

    def call(self, name: str, *args, context=None):
        """Invoke any registered function — Python or native stub."""
        return self.dispatcher.call(name, *args, context=context)

    def has_function(self, name: str) -> bool:
        return self.registry.has_function(name)

    def list_functions(self) -> list:
        return self.registry.list_functions()

    # ── Object handle store ───────────────────────────────────────────────────

    def store_object(self, obj) -> int:
        """Store a non-primitive object; returns an opaque integer handle."""
        return self.store.put(obj)

    def load_object(self, handle: int):
        """Retrieve an object by its handle."""
        return self.store.get(handle)

    def delete_object(self, handle: int):
        """Release an object handle from the store."""
        self.store.delete(handle)

    def call_method(self, handle: int, method: str, *args):
        """Invoke a method on an object held in the store."""
        obj = self.load_object(handle)
        if obj is None:
            raise ValueError(f"[Bridge] Invalid object handle: {handle}")
        return getattr(obj, method)(*args)
