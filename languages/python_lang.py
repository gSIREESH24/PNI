"""
Python language adapter — Milestone A (and the foundation for all others).

Bridge API available inside Python code
─────────────────────────────────────────
  export(name, value)
      Publish a plain value to the shared bridge.  It is immediately
      visible to all later language blocks.

  export_function(name, func)
      Register a Python callable in the global function table.
      Any later Python block (or future in-process adapters) can call it
      via  call(name, *args).

  get_global(name, default=None)
      Read any value that was published to the bridge (from global {},
      a previous Python block, or any other language's exports).

  call(name, *args)
      Invoke a function that was previously registered with
      export_function().  This is the Python-to-Python (and later
      Python-to-Python-via-bridge) call path for Milestone A.

  store_object(obj) -> int
      Store any Python object in the bridge ObjectStore.
      Returns an integer handle that can be passed via export().

  load_object(handle) -> object
      Retrieve a stored object by its integer handle.

  delete_object(handle)
      Release a handle from the ObjectStore.
"""


def run(code: str, context) -> dict:
    exports: dict = {}

    # ── Bridge helpers injected into user code ────────────────────────────

    def export(name: str, value):
        context.set(name, value)
        exports[name] = value

    def export_function(name: str, func, param_types=None, return_type: str = None):
        context.export_function(name, func, language="python",
                                param_types=param_types, return_type=return_type)
        exports[name] = func          # mark as exported so interpreter can log it

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

    # ── Build execution environment ───────────────────────────────────────
    # Seed with every current bridge value (globals + previous exports)
    env: dict = {k: v for k, v in context.all().items()}

    # Inject bridge helpers
    env["export"]          = export
    env["export_function"] = export_function
    env["get_global"]      = get_global
    env["call"]            = call
    env["store_object"]    = store_object
    env["load_object"]     = load_object
    env["delete_object"]   = delete_object

    # remember which keys existed before exec so we can pick up implicit vars
    original_keys = set(env.keys())

    # ── Execute user code ─────────────────────────────────────────────────
    exec(code, env, env)

    # ── Collect any NEW plain variables not already exported ──────────────
    _skip = {"export", "export_function", "get_global", "call",
             "store_object", "load_object", "delete_object"}
    for key, value in env.items():
        if key.startswith("__") or key in _skip:
            continue
        if callable(value) and key not in exports:
            continue                        # don't auto-export bare functions
        if key in original_keys and key not in exports:
            continue                        # don't re-publish unchanged globals
        if key not in exports:
            context.set(key, value)
            exports[key] = value

    return exports