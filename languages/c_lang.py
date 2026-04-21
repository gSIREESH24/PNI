"""
C language adapter — Phase 3 update.

Bridge API available inside C code
────────────────────────────────────
  export_value(name, value)
      A _Generic macro that dispatches to the correct typed printer.
      Supported types: long long, double, _Bool, const char*.

  call_bridge_i(name, args_json)  → long long
  call_bridge_f(name, args_json)  → double
  call_bridge_b(name, args_json)  → int (0/1)
  call_bridge_s(name, args_json)  → const char*  (points into internal buffer)
      Call a Python function registered with export_function().
      args_json is a JSON array string, e.g. "[9]" or "[2, 3]".
      Example:  long long r = call_bridge_i("square", "[9]");

Shared globals are injected as  static const <type> name = value;
before the user's code, so they are available as plain C variables.

Exports are read from stdout lines prefixed with __POLY_EXPORT__.
Format:  __POLY_EXPORT__<name>|<type>|<raw_value>

Function calls use the interactive pipe protocol in bridge/pipe_runner.py.
stdout/stdin are set unbuffered via __attribute__((constructor)) so the
interactive protocol works correctly through a pipe.
"""

import os
import shutil
import subprocess
import uuid

from bridge.pipe_runner import run_interactive

EXPORT_PREFIX = "__POLY_EXPORT__"


# ── C literal helpers ─────────────────────────────────────────────────────────

def _escape_c_string(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
         .replace('"',  '\\"')
         .replace("|",  "\\|")
    )


def _literal_for_c(value):
    """Return (c_literal_string, c_type_string) or None if not supported."""
    if isinstance(value, bool):
        return ("1" if value else "0", "int")
    if value is None:
        return ("0", "int")
    if isinstance(value, int):
        return (str(value), "long long")
    if isinstance(value, float):
        return (repr(value), "double")
    if isinstance(value, str):
        return (f'"{_escape_c_string(value)}"', "char *")
    return None


# ── Preamble builder ──────────────────────────────────────────────────────────

def _build_preamble(context) -> str:
    global_decls: list[str] = []
    if context is not None:
        for key, value in context.all().items():
            if key.startswith("__") or callable(value):
                continue
            result = _literal_for_c(value)
            if result is None:
                continue
            literal, ctype = result
            global_decls.append(f"static const {ctype} {key} = {literal};")

    globals_block = "\n".join(global_decls)

    # ── Inject class schemas (Phase 3D) ───────────────────────────────────
    C_TYPE_MAP = {
        "int": "long long",
        "float": "double",
        "bool": "bool",
        "str": "const char *"
    }
    class_decls: list[str] = []
    if context is not None:
        for cname, cfields in context.bridge.registry.class_schemas.items():
            fields_c = " ".join(f"{C_TYPE_MAP.get(t, 'long long')} {f};" for f, t in cfields.items())
            class_decls.append(f"typedef struct {{ {fields_c} }} {cname};")
            
            macro_lines = [
                f"#define export_value_{cname}(name, obj) do {{ \\",
                f"    printf(\"__POLY_EXPORT__%s|json|{{ \", name); \\"
            ]
            for i, (f, t) in enumerate(cfields.items()):
                comma = "," if i < len(cfields)-1 else ""
                macro_lines.append(f"    printf(\"\\\"{f}\\\":\"); \\")
                if t == "int":
                    macro_lines.append(f"    printf(\"%lld{comma}\", obj.{f}); \\")
                elif t == "float":
                    macro_lines.append(f"    printf(\"%f{comma}\", obj.{f}); \\")
                elif t == "bool":
                    macro_lines.append(f"    printf(\"%s{comma}\", obj.{f} ? \"true\" : \"false\"); \\")
                elif t == "str":
                    macro_lines.append(f"    _poly_json_str(obj.{f}); printf(\"{comma}\"); \\")
            macro_lines.append("    printf(\" }\\n\"); \\")
            macro_lines.append("    fflush(stdout); \\")
            macro_lines.append("} while(0)")
            class_decls.append("\n".join(macro_lines))
    
    classes_block = "\n".join(class_decls)

    return f"""\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/* Forward declaration for class schema exporting */
static void _poly_json_str(const char *s);

/* ── Unbuffer stdout/stdin for interactive pipe protocol ── */
__attribute__((constructor))
static void _poly_unbuffer(void) {{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
}}

/* ── PolyBridge typed export printers ── */
static void _poly_int   (const char *n, long long v) {{ printf("{EXPORT_PREFIX}%s|int|%lld\\n",    n, v); }}
static void _poly_double(const char *n, double    v) {{ printf("{EXPORT_PREFIX}%s|double|%.17g\\n", n, v); }}
static void _poly_bool  (const char *n, int       v) {{ printf("{EXPORT_PREFIX}%s|bool|%s\\n",     n, v ? "true" : "false"); }}
static void _poly_str   (const char *n, const char *v) {{ printf("{EXPORT_PREFIX}%s|string|%s\\n", n, v ? v : ""); }}

#define export_value(name, value) _Generic((value),  \\
    _Bool:        _poly_bool,    \\
    char *:       _poly_str,     \\
    const char *: _poly_str,     \\
    float:        _poly_double,  \\
    double:       _poly_double,  \\
    default:      _poly_int      \\
)(name, value)

/* ── PolyBridge call_bridge helpers ── */
static char __poly_ret_buf[65536];

static void _poly_call_raw(const char *name, const char *args_json) {{
    printf("__POLY_CALL__|%s|%s\\n", name, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin)) {{
        __poly_ret_buf[0] = '\\0';
    }}
}}

/* ── Return parsers ── */
static long long _parse_ret_i() {{
    char *p;
    if ((p = strstr(__poly_ret_buf, "|int|")))   return atoll(p + 5);
    if ((p = strstr(__poly_ret_buf, "|float|"))) return (long long)atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1LL : 0LL;
    return 0;
}}
static double _parse_ret_f() {{
    char *p;
    if ((p = strstr(__poly_ret_buf, "|float|"))) return atof(p + 7);
    if ((p = strstr(__poly_ret_buf, "|int|")))   return (double)atoll(p + 5);
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1.0 : 0.0;
    return 0.0;
}}
static int _parse_ret_b() {{
    char *p;
    if ((p = strstr(__poly_ret_buf, "|bool|")))  return strncmp(p + 6, "true", 4) == 0 ? 1 : 0;
    if ((p = strstr(__poly_ret_buf, "|int|")))   return atoll(p + 5) != 0 ? 1 : 0;
    return 0;
}}
static const char* _parse_ret_s() {{
    char *p = strstr(__poly_ret_buf, "|str|");
    if (!p) return "";
    p += 5;
    size_t len = strlen(p);
    while (len > 0 && (p[len-1] == '\\n' || p[len-1] == '\\r')) {{ p[--len] = '\\0'; }}
    return p;
}}

/* ── Call Bridge Helpers ── */
static long long  call_bridge_i(const char *n, const char *args) {{ _poly_call_raw(n, args); return _parse_ret_i(); }}
static double     call_bridge_f(const char *n, const char *args) {{ _poly_call_raw(n, args); return _parse_ret_f(); }}
static int        call_bridge_b(const char *n, const char *args) {{ _poly_call_raw(n, args); return _parse_ret_b(); }}
static const char* call_bridge_s(const char *n, const char *args) {{ _poly_call_raw(n, args); return _parse_ret_s(); }}

/* ── Phase 3E: Method Proxies ── */
static void _poly_method_raw(long long handle, const char *method, const char *args_json) {{
    printf("__POLY_METHOD__|%lld|%s|%s\\n", handle, method, args_json);
    fflush(stdout);
    if (!fgets(__poly_ret_buf, (int)sizeof(__poly_ret_buf), stdin)) {{
        __poly_ret_buf[0] = '\\0';
    }}
}}
static long long  call_method_i(long long h, const char *m, const char *args) {{ _poly_method_raw(h, m, args); return _parse_ret_i(); }}
static double     call_method_f(long long h, const char *m, const char *args) {{ _poly_method_raw(h, m, args); return _parse_ret_f(); }}
static int        call_method_b(long long h, const char *m, const char *args) {{ _poly_method_raw(h, m, args); return _parse_ret_b(); }}
static const char* call_method_s(long long h, const char *m, const char *args) {{ _poly_method_raw(h, m, args); return _parse_ret_s(); }}

/* ── Milestone 3: export_bridge_function ── */
/* Prints a JSON-encoded source string on stdout so Python can store it as a stub. */
static void _poly_json_str(const char *s) {{
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

/* export_bridge_function(name, source, return_type)
   Registers a C function as a bridge stub callable from Python via call("name", args).
   source      : C function definition as a string literal, e.g.
                 "long long triple(long long x) {{ return x * 3; }}"
   return_type : "int" | "float" | "bool" | "str" */
#define export_bridge_function(name, source, return_type) \\
    do {{ \\
        printf("__POLY_REGISTER__|%s|c|%s|", name, return_type); \\
        _poly_json_str(source); \\
        puts(""); \\
        fflush(stdout); \\
    }} while(0)

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
        except ValueError as e:
            print(f"[Bridge Debug] C JSON parse error: {e} on raw='{raw}'")
            return None
    return {name: raw}


# ── Runner ────────────────────────────────────────────────────────────────────

def run(code: str, context=None) -> dict:
    preamble  = _build_preamble(context)
    full_code = preamble + "\n" + code

    build_dir = os.path.join(os.getcwd(), f"_poly_c_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    c_file  = os.path.join(build_dir, "main.c")
    exe     = os.path.join(build_dir, "main.exe")

    try:
        with open(c_file, "w", encoding="utf-8") as f:
            f.write(full_code)

        cp = subprocess.run(
            ["gcc", "-std=c11", c_file, "-o", exe],
            capture_output=True, text=True,
        )
        if cp.returncode != 0:
            print("[C] Compilation error:")
            print(cp.stderr.strip())
            return {}

        return run_interactive([exe], context, _parse_export_line)

    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
