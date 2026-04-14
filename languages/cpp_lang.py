"""
C++ language adapter — Phase 3 update.

Bridge API available inside C++ code
──────────────────────────────────────
  export_value(name, value)
      Overloaded function in namespace polybridge, brought into scope with
      'using namespace polybridge;'.
      Supported overloads: long long, int, double, bool, const char*, std::string.

  call_bridge<ReturnType>(name, args_json)       — templated, explicit return type
  call_bridge_i(name, args_json)  → long long
  call_bridge_f(name, args_json)  → double
  call_bridge_b(name, args_json)  → bool
  call_bridge_s(name, args_json)  → std::string
      Call a Python function registered with export_function().
      args_json is a JSON array string, e.g. "[9]" or "[2.5, 3.0]".
      Example:  long long r = call_bridge_i("square", "[9]");
               auto r2    = call_bridge<double>("power", "[2.0, 10]");

Shared globals are injected as  static const <type> name = value;
before the user's code.
stdout/stdin are set unbuffered via __attribute__((constructor)).

Exports are read from stdout lines prefixed with __POLY_EXPORT__.
Function calls use the interactive pipe protocol in bridge/pipe_runner.py.
"""

import os
import shutil
import subprocess
import uuid

from bridge.pipe_runner import run_interactive

EXPORT_PREFIX = "__POLY_EXPORT__"


# ── C++ literal helpers ───────────────────────────────────────────────────────

def _escape_cpp_string(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
         .replace('"',  '\\"')
         .replace("|",  "\\|")
    )


def _literal_for_cpp(value):
    """Return (cpp_literal_string, cpp_type_string) or None if not supported."""
    if isinstance(value, bool):
        return ("true" if value else "false", "bool")
    if value is None:
        return ("0", "int")
    if isinstance(value, int):
        return (str(value), "long long")
    if isinstance(value, float):
        return (repr(value), "double")
    if isinstance(value, str):
        return (f'"{_escape_cpp_string(value)}"', "char*")
    return None


# ── Preamble builder ──────────────────────────────────────────────────────────

def _build_preamble(context) -> str:
    global_decls: list[str] = []
    if context is not None:
        for key, value in context.all().items():
            if key.startswith("__") or callable(value):
                continue
            result = _literal_for_cpp(value)
            if result is None:
                continue
            literal, ctype = result
            global_decls.append(f"static const {ctype} {key} = {literal};")

    globals_block = "\n".join(global_decls)

    # ── Inject class schemas (Phase 3D) ───────────────────────────────────
    CPP_TYPE_MAP = {
        "int": "long long",
        "float": "double",
        "bool": "bool",
        "str": "std::string"
    }
    class_decls: list[str] = []
    if context is not None:
        for cname, cfields in context.bridge.registry.class_schemas.items():
            fields_cpp = " ".join(f"{CPP_TYPE_MAP.get(t, 'long long')} {f};" for f, t in cfields.items())
            class_decls.append(f"struct {cname} {{\n    {fields_cpp}\n}};")
            
            # export_value overload in polybridge namespace
            func_lines = [
                f"namespace polybridge {{",
                f"inline void export_value(const std::string& name, const {cname}& obj) {{",
                f"    std::cout << \"__POLY_EXPORT__\" << name << \"|json|{{ \";"
            ]
            for i, (f, t) in enumerate(cfields.items()):
                comma = "," if i < len(cfields)-1 else ""
                func_lines.append(f"    std::cout << \"\\\"{f}\\\":\";")
                if t == "int" or t == "float":
                    func_lines.append(f"    std::cout << obj.{f} << \"{comma}\";")
                elif t == "bool":
                    func_lines.append(f"    std::cout << (obj.{f} ? \"true\" : \"false\") << \"{comma}\";")
                elif t == "str":
                    func_lines.append(f"    _poly_json_str(obj.{f}.c_str()); std::cout << \"{comma}\";")
            func_lines.append("    std::cout << \" }\\n\";")
            func_lines.append("    std::cout.flush();")
            func_lines.append("}")
            func_lines.append("} // namespace polybridge")
            class_decls.append("\n".join(func_lines))
    
    classes_block = "\n".join(class_decls)

    return f"""\
#include <iostream>
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace polybridge {{

/* ── Unbuffer stdout/stdin for interactive pipe protocol ── */
__attribute__((constructor))
static void _poly_unbuffer() {{
    setvbuf(stdout, nullptr, _IONBF, 0);
    setvbuf(stdin,  nullptr, _IONBF, 0);
}}

/* ── export_value overloads ── */
inline void export_value(const std::string& name, long long v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|int|"    << v                    << std::endl;
}}
inline void export_value(const std::string& name, int v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|int|"    << v                    << std::endl;
}}
inline void export_value(const std::string& name, double v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|double|" << v                    << std::endl;
}}
inline void export_value(const std::string& name, bool v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|bool|"   << (v ? "true":"false") << std::endl;
}}
inline void export_value(const std::string& name, const char* v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|string|" << (v ? v : "")         << std::endl;
}}
inline void export_value(const std::string& name, const std::string& v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|string|" << v                    << std::endl;
}}

/* ── call_bridge helpers ── */
static char __poly_ret_buf[65536];

static void _poly_call_raw(const char *name, const char *args_json) {{
    printf("__POLY_CALL__|%s|%s\\n", name, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin)) {{
        __poly_ret_buf[0] = '\\0';
    }}
}}

namespace detail {{

template<typename T> T _parse_ret();

template<> long long _parse_ret() {{
    const char *p;
    if ((p = strstr(__poly_ret_buf, "|int|")))   return (long long)atoll(p + 5);
    if ((p = strstr(__poly_ret_buf, "|float|"))) return (long long)atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1LL : 0LL;
    return 0;
}}
template<> int _parse_ret() {{
    return (int)_parse_ret<long long>();
}}
template<> double _parse_ret() {{
    const char *p;
    if ((p = strstr(__poly_ret_buf, "|float|"))) return atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|int|")))   return (double)atoll(p + 5);
    return 0.0;
}}
template<> bool _parse_ret() {{
    const char *p;
    if ((p = strstr(__poly_ret_buf, "|bool|"))) return strncmp(p + 6, "true", 4) == 0;
    if ((p = strstr(__poly_ret_buf, "|int|"))) return atoll(p + 5) != 0;
    return false;
}}
template<> std::string _parse_ret() {{
    const char *p = strstr(__poly_ret_buf, "|str|");
    if (!p) return "";
    p += 5;
    std::string s(p);
    while (!s.empty() && (s.back() == '\\n' || s.back() == '\\r')) s.pop_back();
    return s;
}}

}} // namespace detail

/* Templated call — explicit return type: call_bridge<long long>("fn", "[9]") */
template<typename R>
R call_bridge(const std::string& name, const std::string& args_json = "[]") {{
    _poly_call_raw(name.c_str(), args_json.c_str());
    return detail::_parse_ret<R>();
}}

/* Convenience named wrappers */
inline long long  call_bridge_i(const std::string& n, const std::string& a="[]") {{ return call_bridge<long long>(n, a); }}
inline double     call_bridge_f(const std::string& n, const std::string& a="[]") {{ return call_bridge<double>(n, a); }}
inline bool       call_bridge_b(const std::string& n, const std::string& a="[]") {{ return call_bridge<bool>(n, a); }}
inline std::string call_bridge_s(const std::string& n, const std::string& a="[]") {{ return call_bridge<std::string>(n, a); }}

/* ── Phase 3E: Method Proxies ── */

static void _poly_method_raw(long long handle, const char *method, const char *args_json) {{
    printf("__POLY_METHOD__|%lld|%s|%s\\n", handle, method, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin)) {{
        __poly_ret_buf[0] = '\\0';
    }}
}}

template<typename R>
R call_method(long long handle, const std::string& method, const std::string& args_json = "[]") {{
    _poly_method_raw(handle, method.c_str(), args_json.c_str());
    return detail::_parse_ret<R>();
}}

inline long long  call_method_i(long long h, const std::string& m, const std::string& a="[]") {{ return call_method<long long>(h, m, a); }}
inline double     call_method_f(long long h, const std::string& m, const std::string& a="[]") {{ return call_method<double>(h, m, a); }}
inline bool       call_method_b(long long h, const std::string& m, const std::string& a="[]") {{ return call_method<bool>(h, m, a); }}
inline std::string call_method_s(long long h, const std::string& m, const std::string& a="[]") {{ return call_method<std::string>(h, m, a); }}

/* ── Milestone 3: export_bridge_function ── */
inline void _poly_json_str(const char *s) {{
    putchar('"');
    for (; *s; ++s) {{
        if      (*s == '"')  {{ putchar('\\\\'); putchar('"');  }}
        else if (*s == '\\\\') {{ putchar('\\\\'); putchar('\\\\'); }}
        else if (*s == '\\n') {{ putchar('\\\\'); putchar('n');  }}
        else if (*s == '\\r') {{ putchar('\\\\'); putchar('r');  }}
        else if (*s == '\\t') {{ putchar('\\\\'); putchar('t');  }}
        else                  {{ putchar(*s); }}
    }}
    putchar('"');
}}

#define export_bridge_function(name, source, return_type) \\
    do {{ \\
        printf("__POLY_REGISTER__|%s|cpp|%s|", name, return_type); \\
        polybridge::_poly_json_str(source); \\
        puts(""); \\
        fflush(stdout); \\
    }} while(0)

}} // namespace polybridge

using namespace polybridge;

/* ── Shared globals from bridge ── */
{globals_block}

/* ── Class schemas from bridge ── */
{classes_block}
"""


# ── Export-line parser ────────────────────────────────────────────────────────

def _parse_export_line(line: str):
    """Return {{name: value}} dict or None."""
    if not line.startswith(EXPORT_PREFIX):
        return None
    payload = line[len(EXPORT_PREFIX):]
    parts   = payload.split("|", 2)
    if len(parts) != 3:
        return None
    name, type_name, raw = parts
    if type_name == "int":
        try:    return {name: int(raw)}
        except ValueError: return None
    if type_name == "double":
        try:    return {name: float(raw)}
        except ValueError: return None
    if type_name == "bool":
        return {name: raw.lower() == "true"}
    if type_name == "string":
        return {name: (raw.replace("\\|", "|")
                          .replace("\\n", "\n")
                          .replace("\\r", "\r")
                          .replace("\\\\", "\\"))}
    if type_name == "json":
        try:
            import json
            return {name: json.loads(raw)}
        except ValueError:
            return None
    return {name: raw}


# ── Runner ────────────────────────────────────────────────────────────────────

def run(code: str, context=None) -> dict:
    preamble  = _build_preamble(context)
    full_code = preamble + "\n" + code

    build_dir = os.path.join(os.getcwd(), f"_poly_cpp_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    cpp_file = os.path.join(build_dir, "main.cpp")
    exe      = os.path.join(build_dir, "main.exe")

    try:
        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(full_code)

        cp = subprocess.run(
            ["g++", "-std=c++17", cpp_file, "-o", exe],
            capture_output=True, text=True,
        )
        if cp.returncode != 0:
            print("[C++] Compilation error:")
            print(cp.stderr.strip())
            return {}

        return run_interactive([exe], context, _parse_export_line)

    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
