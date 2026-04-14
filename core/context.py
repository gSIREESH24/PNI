from bridge import PolyBridge


class Context:
    """
    Thin runtime wrapper around PolyBridge.

    This is the object passed to every language adapter during execution.
    It delegates all storage and dispatch to the single shared PolyBridge.

    Supported operations
    ─────────────────────
      set(key, value)                   — publish a value to the bridge
      get(key)                          — read a value from the bridge
      all()                             — snapshot of all current values
      export_function(name, fn, ...)    — register a Python function globally
      get_function(name)                — retrieve registered function callable
      has_function(name)                — check if a function is registered
      call(name, *args)                 — invoke a function through the dispatcher
      store_object(obj) → handle        — put an object in the handle store
      load_object(handle)               — retrieve by handle
      delete_object(handle)             — release a handle
    """

    def __init__(self, bridge: PolyBridge = None):
        self.bridge = bridge if bridge is not None else PolyBridge()

    # ── Values ────────────────────────────────────────────────────────────

    def set(self, key: str, value):
        self.bridge.set(key, value)

    def get(self, key: str, default=None):
        return self.bridge.get(key, default)

    def all(self) -> dict:
        return self.bridge.all_values()

    # ── Functions ─────────────────────────────────────────────────────────

    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type=None):
        self.bridge.export_function(
            name, func, language, param_types, return_type
        )

    def export_class_schema(self, name: str, fields: dict[str, str]):
        self.bridge.export_class_schema(name, fields)

    def get_function(self, name: str):
        entry = self.bridge.registry.get_function(name)
        return entry.func if entry is not None else None

    def has_function(self, name: str) -> bool:
        return self.bridge.has_function(name)

    def register_function_stub(self, name: str, language: str, source: str,
                               return_type: str = "int"):
        """Register a subprocess-language function stub (Milestone 3)."""
        self.bridge.register_function_stub(name, language, source, return_type)

    def call(self, name: str, *args):
        return self.bridge.call(name, *args)

    # ── Object handles ────────────────────────────────────────────────────

    def store_object(self, obj) -> int:
        return self.bridge.store_object(obj)

    def load_object(self, handle: int):
        return self.bridge.load_object(handle)

    def delete_object(self, handle: int):
        self.bridge.delete_object(handle)

    def call_method(self, handle: int, method: str, *args):
        return self.bridge.call_method(handle, method, *args)