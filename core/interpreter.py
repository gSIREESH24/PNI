import ast as py_ast
from core.context import Context
from languages import LANGUAGE_REGISTRY


def interpret(program_node):
    """
    Phase-2 Interpreter — acts as the coordinator, not a direct executor.

    Flow for each block:
      1. global { }   → parse key=value pairs → store in bridge
      2. lang { }     → send to language adapter → receive exports dict
      3. sync exports → write every exported key/value back into bridge
                        so the NEXT block sees them

    This sync-after-every-block makes the runtime polyglot.
    """
    context = Context()
    print("\n=== Phase-2 Polyglot Runtime ===\n")

    for block in program_node.blocks:
        lang = block.language
        code = block.code

        print(f"--- [{lang.upper()}] ---", flush=True)

        # ── Global block ──────────────────────────────────────────────────
        if lang == "global":
            process_global(code, context)
            keys = list(context.all().keys())
            print(f"[Bridge] globals loaded: {keys}")
            continue

        # ── Language block ────────────────────────────────────────────────
        runner = LANGUAGE_REGISTRY.get(lang)
        if runner is None:
            print(f"[Bridge] ERROR — unsupported language: '{lang}'", flush=True)
            continue

        try:
            result = runner(code, context)
            exports = result[0] if isinstance(result, tuple) else result
        except Exception as exc:
            print(f"[Bridge] ERROR in {lang} block: {exc}", flush=True)
            exports = {}

        # ── Sync exports into shared bridge ───────────────────────────────
        if isinstance(exports, dict):
            for key, value in exports.items():
                context.set(key, value)
                if callable(value):
                    print(f"[Bridge] {lang} registered function: {key!r}")
                else:
                    print(f"[Bridge] {lang} exported: {key} = {value!r}")

    print("\n=== Final Bridge State ===")
    for k, v in sorted(context.all().items()):
        if not callable(v):
            print(f"  {k} = {v!r}")
    fns = context.bridge.list_functions()
    if fns:
        print(f"  registered functions: {fns}")


def process_global(code: str, context: Context):
    """
    Parse a global { } block.

    Supports lines of the form:
        key = <Python literal>    (int, float, bool, string, list)
    Lines starting with # and blank lines are ignored.
    """
    for line in code.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, raw_value = line.partition("=")
        key       = key.strip()
        raw_value = raw_value.strip()

        try:
            parsed_value = py_ast.literal_eval(raw_value)
        except Exception:
            parsed_value = raw_value          # treat as plain string

        context.set(key, parsed_value)