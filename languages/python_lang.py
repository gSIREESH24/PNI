def run(code: str, context) -> dict:
    exports: dict = {}

    def export(name: str, value):
        context.set(name, value)
        exports[name] = value

    def export_function(name: str, func, param_types=None, return_type: str = None):
        context.export_function(name, func, language="python",
                                param_types=param_types, return_type=return_type)
        exports[name] = func

    def export_class(name: str, cls, fields: dict[str, str]):
        context.export_class_schema(name, fields)
        exports[name] = cls

    def get_global(name: str, default=None):
        v = context.get(name)
        return default if v is None else v

    def call(name: str, *args):
        if not context.has_function(name):
            raise NameError(f"[Bridge] Function '{name}' is not registered.")
        return context.call(name, *args)

    def store_object(obj) -> int:
        return context.store_object(obj)

    def load_object(handle: int):
        return context.load_object(handle)

    def delete_object(handle: int):
        context.delete_object(handle)

    env: dict = {k: v for k, v in context.all().items()}

    env["export"]          = export
    env["export_function"] = export_function
    env["export_class"]    = export_class
    env["get_global"]      = get_global
    env["call"]            = call
    env["store_object"]    = store_object
    env["load_object"]     = load_object
    env["delete_object"]   = delete_object

    original_keys = set(env.keys())

    exec(code, env, env)

    _skip = {"export", "export_function", "get_global", "call",
             "store_object", "load_object", "delete_object"}
    for key, value in env.items():
        if key.startswith("__") or key in _skip:
            continue
        if callable(value) and key not in exports:
            continue
        if key in original_keys and key not in exports:
            continue
        if key not in exports:
            context.set(key, value)
            exports[key] = value

    return exports