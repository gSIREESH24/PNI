"""
C++ language adapter — Milestone C (cont.)

Bridge API available inside C++ code
──────────────────────────────────────
  export_value(name, value)
      Overloaded function in namespace polybridge, brought into scope with
      'using namespace polybridge;'.
      Supported overloads: long long, int, double, bool, const char*, std::string.

Shared globals are injected as  static const <type> name = value;
before the user's code.

Exports are read from stdout lines prefixed with __POLY_EXPORT__.
"""

import os
import shutil
import subprocess
import uuid

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
        # Use 'char*' here — we add 'static const' as a prefix in _build_preamble
        # so writing 'const char*' would produce 'static const const char*' (invalid)
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

    return f"""\
#include <iostream>
#include <string>

namespace polybridge {{

inline void export_value(const std::string& name, long long v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|int|"    << v                     << std::endl;
}}
inline void export_value(const std::string& name, int v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|int|"    << v                     << std::endl;
}}
inline void export_value(const std::string& name, double v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|double|" << v                     << std::endl;
}}
inline void export_value(const std::string& name, bool v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|bool|"   << (v ? "true":"false")  << std::endl;
}}
inline void export_value(const std::string& name, const char* v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|string|" << (v ? v : "")          << std::endl;
}}
inline void export_value(const std::string& name, const std::string& v) {{
    std::cout << "{EXPORT_PREFIX}" << name << "|string|" << v                     << std::endl;
}}

}} // namespace polybridge

using namespace polybridge;

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

    build_dir = os.path.join(os.getcwd(), f"_poly_cpp_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    cpp_file = os.path.join(build_dir, "main.cpp")
    exe      = os.path.join(build_dir, "main.exe")
    exports: dict = {}

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
