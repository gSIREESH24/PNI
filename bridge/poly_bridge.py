from .registry import Registry
from .object_store import ObjectStore
from .dispatcher import Dispatcher
from .poly_value import PolyValue


class PolyBridge:
    """
    The central Phase-2 bridge.

    This is the single interface that all language adapters talk through.
    It owns:
      - registry   : shared global values and registered functions
      - store      : handle-based object storage for non-primitives
      - dispatcher : routes call(name, args) to the right Python function

    Design principle: no language talks directly to another language.
    Every value and every call goes through this bridge.
    """

    def __init__(self):
        self.registry   = Registry()
        self.store      = ObjectStore()
        self.dispatcher = Dispatcher(self.registry)

    # ── Values ────────────────────────────────────────────────────────────

    def set(self, name: str, value):
        """Publish a plain Python value to the shared registry."""
        self.registry.set_value(name, value)

    def get(self, name: str, default=None):
        """Read a plain Python value from the shared registry."""
        return self.registry.get_value(name, default)

    def all_values(self) -> dict:
        """Return a snapshot of all current shared values."""
        return dict(self.registry.values)

    # ── Functions ─────────────────────────────────────────────────────────

    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type: str = None):
        """Register a callable in the global function table."""
        self.registry.export_function(name, func, language, param_types, return_type)

    def export_class_schema(self, name: str, fields: dict[str, str]):
        """Register a class schema for code-generation in other languages."""
        self.registry.export_class_schema(name, fields)

    def register_function_stub(self, name: str, language: str, source: str,
                               return_type: str = "int"):
        """Register a subprocess-language function stub (Milestone 3)."""
        self.registry.register_stub(name, language, source, return_type)

    def call(self, name: str, *args, context=None):
        """Invoke a registered function by name through the dispatcher."""
        return self.dispatcher.call(name, *args, context=context)

    def has_function(self, name: str) -> bool:
        return self.registry.has_function(name)

    def list_functions(self) -> list:
        return self.registry.list_functions()

    # ── Object handles ────────────────────────────────────────────────────

    def store_object(self, obj) -> int:
        """Store a non-primitive object; returns an integer handle."""
        return self.store.put(obj)

    def load_object(self, handle: int):
        """Retrieve an object by its handle."""
        return self.store.get(handle)

    def delete_object(self, handle: int):
        """Release an object handle."""
        self.store.delete(handle)

    def call_method(self, handle: int, method: str, *args):
        """Invoke a method on an object stored in the object store."""
        obj = self.load_object(handle)
        if obj is None:
            raise ValueError(f"Invalid object handle: {handle}")
        func = getattr(obj, method)
        return func(*args)
