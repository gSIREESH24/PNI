"""
C language adapter — Milestone C.

Bridge API available inside C code
────────────────────────────────────
  export_value(name, value)
      A _Generic macro that dispatches to the correct typed printer.
      Supported types: long long, double, _Bool, const char *.

Shared globals are injected as  static const <type> name = value;
before the user's code, so they are available as plain C variables.

Exports are read from stdout lines prefixed with __POLY_EXPORT__.
Format:  __POLY_EXPORT__<name>|<type>|<raw_value>
"""

import os
import shutil
import subprocess
import uuid

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
    if isinstance(value, bool):        # must come before int check
        return ("1" if value else "0", "int")
    if value is None:
        return ("0", "int")
    if isinstance(value, int):
        return (str(value), "long long")
    if isinstance(value, float):
        return (repr(value), "double")
    if isinstance(value, str):
        # Use 'char *' — 'static const' prefix already makes it read-only
        # writing 'const char *' would produce 'static const const char *' (invalid)
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

    return f"""\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/* ── PolyBridge typed printers ── */
static void _poly_int   (const char *n, long long v) {{ printf("{EXPORT_PREFIX}%s|int|%lld\\n",    n, v); }}
static void _poly_double(const char *n, double    v) {{ printf("{EXPORT_PREFIX}%s|double|%.17g\\n", n, v); }}
static void _poly_bool  (const char *n, int       v) {{ printf("{EXPORT_PREFIX}%s|bool|%s\\n",     n, v ? "true" : "false"); }}
static void _poly_str   (const char *n, const char *v) {{ printf("{EXPORT_PREFIX}%s|string|%s\\n", n, v ? v : ""); }}

/* export_value(name, value) — picks the right printer via _Generic */
#define export_value(name, value) _Generic((value),  \\
    _Bool:        _poly_bool,    \\
    char *:       _poly_str,     \\
    const char *: _poly_str,     \\
    float:        _poly_double,  \\
    double:       _poly_double,  \\
    default:      _poly_int      \\
)(name, value)

/* ── Shared globals from bridge ── */
{globals_block}
"""


# ── Export-line parser ────────────────────────────────────────────────────────

def _parse_export_line(line: str):
    if not line.startswith(EXPORT_PREFIX):
        return None
    payload = line[len(EXPORT_PREFIX):]
    parts   = payload.split("|", 2)
    if len(parts) != 3:
        return None
    name, type_name, raw = parts
    if type_name == "int":
        try:    return name, int(raw)
        except ValueError: return None
    if type_name == "double":
        try:    return name, float(raw)
        except ValueError: return None
    if type_name == "bool":
        return name, raw.lower() == "true"
    if type_name == "string":
        return name, (raw.replace("\\|", "|")
                         .replace("\\n", "\n")
                         .replace("\\r", "\r")
                         .replace("\\\\", "\\"))
    return name, raw


# ── Runner ────────────────────────────────────────────────────────────────────

def run(code: str, context=None) -> dict:
    preamble  = _build_preamble(context)
    full_code = preamble + "\n" + code

    build_dir = os.path.join(os.getcwd(), f"_poly_c_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    c_file  = os.path.join(build_dir, "main.c")
    exe     = os.path.join(build_dir, "main.exe")
    exports: dict = {}

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

        rp = subprocess.run([exe], capture_output=True, text=True)

        for line in rp.stdout.splitlines():
            parsed = _parse_export_line(line.strip())
            if parsed is not None:
                exports[parsed[0]] = parsed[1]
            else:
                print(line)

        if rp.stderr:
            print(rp.stderr.rstrip())

        return exports

    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
