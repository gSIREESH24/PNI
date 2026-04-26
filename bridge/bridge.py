from .function_registry import FunctionRegistry
from .object_store      import ObjectStore
from .dispatcher        import Dispatcher


class Bridge:

    def __init__(self):
        self.registry   = FunctionRegistry()
        self.store      = ObjectStore()
        self.dispatcher = Dispatcher(self.registry)

    def set(self, name: str, value):
        self.registry.set_value(name, value)

    def get(self, name: str, default=None):
        return self.registry.get_value(name, default)

    def all_values(self) -> dict:
        return dict(self.registry.values)

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type: str = None):
        self.registry.register_python_function(name, func, param_types, return_type)

    def register_class_schema(self, name: str, fields: dict[str, str]):
        self.registry.register_class_schema(name, fields)

    def register_stub(self, name: str, language: str, source: str,
                      return_type: str = "int"):
        self.registry.register_stub(name, language, source, return_type)

    def call(self, name: str, *args, context=None):
        return self.dispatcher.call(name, *args, context=context)

    def has_function(self, name: str) -> bool:
        return self.registry.has_function(name)

    def list_functions(self) -> list:
        return self.registry.list_functions()

    def store_object(self, obj) -> int:
        return self.store.put(obj)

    def load_object(self, handle: int):
        return self.store.get(handle)

    def delete_object(self, handle: int):
        self.store.delete(handle)

    def call_method(self, handle: int, method: str, *args):
        obj = self.load_object(handle)
        if obj is None:
            raise ValueError(f"[Bridge] Invalid object handle: {handle}")
        return getattr(obj, method)(*args)
