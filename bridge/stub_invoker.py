"""
stub_invoker.py — Universal Vice-Versa stub execution.

When a function registered by JS / C / C++ / Java is called, we construct
a tiny wrapper script that calls the function and logs the result using __POLY_RET__.
This snippet is then passed directly to the corresponding language runner
(e.g., c_lang.run()), which injects the full bridge prelude.

This guarantees the stub environment has `call_bridge()` and can safely
call BACK into the bridge — unlocking infinite recursive vice-versa calling.
"""

from languages import js_lang, c_lang, cpp_lang, java_lang


# ── Python-value → language-literal helpers ───────────────────────────────────

def _to_c_literal(v) -> str:
    if v is None:          return "0"
    if isinstance(v, bool): return "1" if v else "0"
    if isinstance(v, int):  return f"{v}LL"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = (v.replace("\\", "\\\\")
                .replace('"',  '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r"))
        return f'"{esc}"'
    return "0"

def _c_args(args: list) -> str:
    return ", ".join(_to_c_literal(a) for a in args)


def _to_java_literal(v) -> str:
    if v is None:          return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, int):  return f"{v}L"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = (v.replace("\\", "\\\\")
                .replace('"',  '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r"))
        return f'"{esc}"'
    return "null"

def _java_args(args: list) -> str:
    return ", ".join(_to_java_literal(a) for a in args)


# ── Per-language invokers ─────────────────────────────────────────────────────

def _invoke_js(fn_name: str, source: str, args: list, return_type: str, context):
    import json
    args_json = json.dumps(args)
    script = f"""\
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
    result = js_lang.run(script, context)
    return result[1] if isinstance(result, tuple) else None


def _invoke_c(fn_name: str, source: str, args: list, return_type: str, context):
    rt = return_type or "int"
    args_c = _c_args(args)

    if rt == "float":
        call_expr = f"(double)({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|float|%.17g\\n", {call_expr});'
    elif rt == "bool":
        call_expr = f"({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|bool|%s\\n", {call_expr} ? "true" : "false");'
    elif rt == "str":
        call_expr = f"({fn_name}({args_c}))"
        print_stmt = f'{{ const char* __s = {call_expr}; printf("__POLY_RET__|str|%s\\n", __s ? __s : ""); }}'
    else:  # int / default
        call_expr = f"(long long)({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|int|%lld\\n", {call_expr});'

    c_src = f"""\
{source}

int main(void) {{
    {print_stmt}
    return 0;
}}
"""
    result = c_lang.run(c_src, context)
    return result[1] if isinstance(result, tuple) else None


def _invoke_cpp(fn_name: str, source: str, args: list, return_type: str, context):
    rt = return_type or "int"
    args_c = _c_args(args)   # C++ literals are the same as C literals here

    if rt == "float":
        call_expr  = f"(double)({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|float|%.17g\\n", {call_expr});'
    elif rt == "bool":
        call_expr  = f"({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|bool|%s\\n", {call_expr} ? "true" : "false");'
    elif rt == "str":
        call_expr  = f"({fn_name}({args_c}))"
        print_stmt = f'{{ auto __s = {call_expr}; printf("__POLY_RET__|str|%s\\n", __s.c_str()); }}'
    else:
        call_expr  = f"(long long)({fn_name}({args_c}))"
        print_stmt = f'printf("__POLY_RET__|int|%lld\\n", {call_expr});'

    cpp_src = f"""\
{source}

int main() {{
    {print_stmt}
    return 0;
}}
"""
    result = cpp_lang.run(cpp_src, context)
    return result[1] if isinstance(result, tuple) else None


def _invoke_java(fn_name: str, source: str, args: list, return_type: str, context):
    rt = return_type or "int"
    args_j = _java_args(args)

    if rt == "float":
        call_expr  = f"(double)({fn_name}({args_j}))"
        print_stmt = f'System.out.println("__POLY_RET__|float|" + {call_expr});'
    elif rt == "bool":
        call_expr  = f"({fn_name}({args_j}))"
        print_stmt = f'System.out.println("__POLY_RET__|bool|" + ({call_expr} ? "true" : "false"));'
    elif rt == "str":
        call_expr  = f"String.valueOf({fn_name}({args_j}))"
        print_stmt = f'System.out.println("__POLY_RET__|str|" + {call_expr});'
    else:
        call_expr  = f"(long)({fn_name}({args_j}))"
        print_stmt = f'System.out.println("__POLY_RET__|int|" + {call_expr});'

    java_src = f"""\
public class Main {{
    {source}

    public static void main(java.lang.String[] __a) {{
        {print_stmt}
    }}
}}
"""
    result = java_lang.run(java_src, context)
    return result[1] if isinstance(result, tuple) else None


# ── Public entry point ────────────────────────────────────────────────────────

def invoke(fn_name: str, language: str, source: str, return_type: str, args: list, context=None):
    """
    Re-invoke a registered subprocess function by compiling it through the full
    language adapter. This injects all bridge helpers.
    """
    lang = language.lower()
    if lang == "js":
        return _invoke_js(fn_name, source, args, return_type, context)
    if lang == "c":
        return _invoke_c(fn_name, source, args, return_type, context)
    if lang in ("cpp", "c++"):
        return _invoke_cpp(fn_name, source, args, return_type, context)
    if lang == "java":
        return _invoke_java(fn_name, source, args, return_type, context)
    raise ValueError(f"[Bridge] stub_invoker: unsupported language '{language}'")
