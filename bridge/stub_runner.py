"""
stub_runner.py — Executes native-language function stubs on demand.

When Python calls a function that was registered by a subprocess language
(C, C++, JS, Java), we build a tiny wrapper snippet that calls the function
and emits a __POLY_RET__ return line, then feeds it through the generic
language runner.  This injects the full bridge template so the stub can
itself call back into Python — enabling recursive cross-language calls.
"""

import json


def _run(lang: str, code: str, context):
    """Lazy import — avoids the circular import cycle with bridge/__init__.py."""
    from languages.runner import run
    return run(lang, code, context)


# ── Python value → native literal converters ──────────────────────────────────

def _c_literal(v) -> str:
    if v is None:            return "0"
    if isinstance(v, bool):  return "1" if v else "0"
    if isinstance(v, int):   return f"{v}LL"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = v.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n").replace("\r","\\r")
        return f'"{esc}"'
    return "0"

def _c_args(args: list) -> str:
    return ", ".join(_c_literal(a) for a in args)


def _java_literal(v) -> str:
    if v is None:            return "null"
    if isinstance(v, bool):  return "true" if v else "false"
    if isinstance(v, int):   return f"{v}L"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = v.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n").replace("\r","\\r")
        return f'"{esc}"'
    return "null"

def _java_args(args: list) -> str:
    return ", ".join(_java_literal(a) for a in args)


# ── Per-language stub wrappers ────────────────────────────────────────────────

def _run_js_stub(fn_name, source, args, return_type, context):
    args_json = json.dumps(args)
    snippet = f"""\
{source}
(function() {{
  var __args = {args_json};
  var __r = __stub_fn.apply(null, __args);
  var __t = typeof __r;
  if (__r === null || __r === undefined) {{
    process.stdout.write("__POLY_RET__|null|null\\n");
  }} else if (__t === "boolean") {{
    process.stdout.write("__POLY_RET__|bool|" + __r + "\\n");
  }} else if (__t === "number") {{
    if (Number.isInteger(__r))
      process.stdout.write("__POLY_RET__|int|"   + __r + "\\n");
    else
      process.stdout.write("__POLY_RET__|float|" + __r + "\\n");
  }} else {{
    process.stdout.write("__POLY_RET__|str|" + String(__r) + "\\n");
  }}
}})();
"""
    result = _run("javascript", snippet, context)
    return result[1] if isinstance(result, tuple) else None


def _run_c_stub(fn_name, source, args, return_type, context):
    rt, args_c = return_type or "int", _c_args(args)
    if rt == "float":
        stmt = f'printf("__POLY_RET__|float|%.17g\\n", (double)({fn_name}({args_c})));'
    elif rt == "bool":
        stmt = f'printf("__POLY_RET__|bool|%s\\n", ({fn_name}({args_c})) ? "true" : "false");'
    elif rt == "str":
        stmt = f'{{ const char* __s = ({fn_name}({args_c})); printf("__POLY_RET__|str|%s\\n", __s ? __s : ""); }}'
    else:
        stmt = f'printf("__POLY_RET__|int|%lld\\n", (long long)({fn_name}({args_c})));'
    snippet = f"{source}\nint main(void) {{ {stmt} return 0; }}\n"
    result = _run("c", snippet, context)
    return result[1] if isinstance(result, tuple) else None


def _run_cpp_stub(fn_name, source, args, return_type, context):
    rt, args_c = return_type or "int", _c_args(args)
    if rt == "float":
        stmt = f'printf("__POLY_RET__|float|%.17g\\n", (double)({fn_name}({args_c})));'
    elif rt == "bool":
        stmt = f'printf("__POLY_RET__|bool|%s\\n", ({fn_name}({args_c})) ? "true" : "false");'
    elif rt == "str":
        stmt = f'{{ auto __s = ({fn_name}({args_c})); printf("__POLY_RET__|str|%s\\n", __s.c_str()); }}'
    else:
        stmt = f'printf("__POLY_RET__|int|%lld\\n", (long long)({fn_name}({args_c})));'
    snippet = f"{source}\nint main() {{ {stmt} return 0; }}\n"
    result = _run("cpp", snippet, context)
    return result[1] if isinstance(result, tuple) else None


def _run_java_stub(fn_name, source, args, return_type, context):
    rt, args_j = return_type or "int", _java_args(args)
    if rt == "float":
        stmt = f'System.out.println("__POLY_RET__|float|" + (double)({fn_name}({args_j})));'
    elif rt == "bool":
        stmt = f'System.out.println("__POLY_RET__|bool|" + (({fn_name}({args_j})) ? "true" : "false"));'
    elif rt == "str":
        stmt = f'System.out.println("__POLY_RET__|str|" + String.valueOf({fn_name}({args_j})));'
    else:
        stmt = f'System.out.println("__POLY_RET__|int|" + (long)({fn_name}({args_j})));'
    snippet = (
        f"public class Main {{\n"
        f"    {source}\n"
        f"    public static void main(java.lang.String[] __a) {{ {stmt} }}\n"
        f"}}\n"
    )
    result = _run("java", snippet, context)
    return result[1] if isinstance(result, tuple) else None


# ── Public entry point ────────────────────────────────────────────────────────

def invoke(fn_name: str, language: str, source: str, return_type: str,
           args: list, context=None):
    """
    Re-execute a registered native-language function as a fresh subprocess.
    Called by Dispatcher when a Python-side call targets a subprocess stub.
    """
    lang = language.lower()
    if lang == "js":              return _run_js_stub  (fn_name, source, args, return_type, context)
    if lang == "c":               return _run_c_stub   (fn_name, source, args, return_type, context)
    if lang in ("cpp", "c++"):    return _run_cpp_stub (fn_name, source, args, return_type, context)
    if lang == "java":            return _run_java_stub(fn_name, source, args, return_type, context)
    raise ValueError(f"[Bridge] stub_runner: unsupported language '{language}'")
