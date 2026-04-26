"""
context.py — Thin runtime wrapper passed to every language adapter.

Delegates all storage and dispatch to the shared Bridge instance.
Language adapters never touch Bridge directly — they go through Context.
"""

from bridge import Bridge


class Context:
    """
    Per-execution context given to each language block.

    Wraps a shared Bridge so adapters have a clean, minimal API:

      set / get / all         — shared scalar values
      register_python_function— register a Python callable
      register_class_schema   — register a class layout for native codegen
      has_function / call     — function lookup and invocation
      register_function_stub  — store a native-language stub
      store_object            — put a Python object in the handle store
      load_object             — retrieve by handle
      delete_object           — release a handle
      call_method             — invoke a method on a stored object
    """

    def __init__(self, bridge: Bridge = None):
        self.bridge = bridge if bridge is not None else Bridge()

    # ── Shared values ─────────────────────────────────────────────────────────

    def set(self, key: str, value):
        self.bridge.set(key, value)

    def get(self, key: str, default=None):
        return self.bridge.get(key, default)

    def all(self) -> dict:
        return self.bridge.all_values()

    # ── Functions ─────────────────────────────────────────────────────────────

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    # Keep the old name as an alias so python_lang.py doesn't need changes.
    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    def register_class_schema(self, name: str, fields: dict[str, str]):
        self.bridge.register_class_schema(name, fields)

    # Keep old alias used by python_lang.py.
    def export_class_schema(self, name: str, fields: dict[str, str]):
        self.bridge.register_class_schema(name, fields)

    def has_function(self, name: str) -> bool:
        return self.bridge.has_function(name)

    def get_function(self, name: str):
        entry = self.bridge.registry.get_function(name)
        return entry.func if entry is not None else None

    def register_function_stub(self, name: str, language: str, source: str,
                               return_type: str = "int"):
        self.bridge.register_stub(name, language, source, return_type)

    def call(self, name: str, *args):
        return self.bridge.call(name, *args, context=self)

    # ── Object handle store ───────────────────────────────────────────────────

    def store_object(self, obj) -> int:
        return self.bridge.store_object(obj)

    def load_object(self, handle: int):
        return self.bridge.load_object(handle)

    def delete_object(self, handle: int):
        self.bridge.delete_object(handle)

    def call_method(self, handle: int, method: str, *args):
        return self.bridge.call_method(handle, method, *args)