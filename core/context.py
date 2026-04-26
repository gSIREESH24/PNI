from bridge import Bridge


class Context:

    def __init__(self, bridge: Bridge = None):
        self.bridge = bridge if bridge is not None else Bridge()

    def set(self, key: str, value):
        self.bridge.set(key, value)

    def get(self, key: str, default=None):
        return self.bridge.get(key, default)

    def all(self) -> dict:
        return self.bridge.all_values()

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    def register_class_schema(self, name: str, fields: dict[str, str]):
        self.bridge.register_class_schema(name, fields)

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

    def store_object(self, obj) -> int:
        return self.bridge.store_object(obj)

    def load_object(self, handle: int):
        return self.bridge.load_object(handle)

    def delete_object(self, handle: int):
        self.bridge.delete_object(handle)

    def call_method(self, handle: int, method: str, *args):
        return self.bridge.call_method(handle, method, *args)