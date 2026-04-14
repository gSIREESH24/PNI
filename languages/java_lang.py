"""
Java language adapter — Milestone D.

Bridge API available inside Java code
───────────────────────────────────────
  export_value(String name, <type> value)
      Overloaded static method supporting: int, long, double, boolean, String, Object.
      Prints a __POLY_EXPORT__ marker to stdout.

  get_global(String name)
      Returns the bridge value stored under that name as an Object,
      or null if not present.

Shared globals are injected as static final fields inside the Main class.
A static initialiser block populates __globals for get_global() lookups.

Two wrapping modes
───────────────────
  (a) User wrote a bare code body      → wrapped inside Main.main()
  (b) User wrote  class Main { ... }   → bridge is injected inside the class body
"""

import os
import re
import shutil
import subprocess
import textwrap
import uuid

EXPORT_PREFIX = "__POLY_EXPORT__"


# ── Java-string escaping ──────────────────────────────────────────────────────

def _escape_java(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("\n", "\\n")
         .replace("\r", "\\r")
         .replace('"',  '\\"')
         .replace("|",  "\\|")
    )


# ── Bridge injection builder ──────────────────────────────────────────────────

def _build_bridge_members(context) -> str:
    """
    Returns Java source for static fields + static initialiser + helper methods.
    This block is injected at the TOP of the Main class body.
    """
    field_lines: list[str] = []
    map_puts:    list[str] = []

    if context is not None:
        for key, value in context.all().items():
            if key.startswith("__") or callable(value):
                continue
            if isinstance(value, bool):
                jval = str(value).lower()
                field_lines.append(f"    static final boolean {key} = {jval};")
                map_puts.append(f'        __globals.put("{key}", {key});')
            elif isinstance(value, int):
                field_lines.append(f"    static final long {key} = {value}L;")
                map_puts.append(f'        __globals.put("{key}", {key});')
            elif isinstance(value, float):
                field_lines.append(f"    static final double {key} = {repr(value)};")
                map_puts.append(f'        __globals.put("{key}", {key});')
            elif isinstance(value, str):
                esc = _escape_java(value)
                field_lines.append(f'    static final String {key} = "{esc}";')
                map_puts.append(f'        __globals.put("{key}", {key});')

    fields     = "\n".join(field_lines)
    puts_block = "\n".join(map_puts) if map_puts else "        // no globals"

    return f"""\
    /* ── PolyBridge: shared globals ── */
{fields}

    private static final java.util.Map<String,Object> __globals = new java.util.HashMap<>();
    static {{
{puts_block}
    }}

    public static Object get_global(String name) {{
        return __globals.get(name);
    }}

    /* ── PolyBridge: export_value overloads ── */
    public static void export_value(String name, int value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|int|" + value);
    }}
    public static void export_value(String name, long value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|int|" + value);
    }}
    public static void export_value(String name, double value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|double|" + value);
    }}
    public static void export_value(String name, boolean value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|bool|" + value);
    }}
    public static void export_value(String name, String value) {{
        String safe = (value == null) ? "" : value
            .replace("\\\\", "\\\\\\\\")
            .replace("|",    "\\\\|")
            .replace("\\n",  "\\\\n")
            .replace("\\r",  "\\\\r");
        System.out.println("{EXPORT_PREFIX}" + name + "|string|" + safe);
    }}
    public static void export_value(String name, Object value) {{
        export_value(name, value == null ? "null" : String.valueOf(value));
    }}
"""


# ── Code wrapper ──────────────────────────────────────────────────────────────

def _wrap(code: str, bridge_members: str) -> str:
    """
    Produce a complete Main.java source.

    If the user already wrote  class Main { ... }  we inject bridge_members
    right after the opening brace.  Otherwise we wrap the bare body.
    """
    stripped = textwrap.dedent(code).strip()

    # Detect full class definition
    m = re.search(r"(class\s+Main\s*\{)", stripped)
    if m:
        pos = m.end()
        return stripped[:pos] + "\n" + bridge_members + stripped[pos:]

    # Wrap bare body
    body = textwrap.indent(stripped, " " * 8)
    return (
        "public class Main {\n"
        + bridge_members + "\n"
        + "    public static void main(String[] args) {\n"
        + body + "\n"
        + "    }\n"
        + "}\n"
    )


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

def run(text: str, context=None) -> dict:
    bridge_members = _build_bridge_members(context)
    java_source    = _wrap(text, bridge_members)

    temp_dir = os.path.join(os.getcwd(), f"_poly_java_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    exports: dict = {}

    try:
        java_file = os.path.join(temp_dir, "Main.java")
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(java_source)

        cp = subprocess.run(
            ["javac", "-encoding", "UTF-8", java_file],
            capture_output=True, text=True,
        )
        if cp.returncode != 0:
            print("[Java] Compilation error:")
            print(cp.stderr.strip())
            return {}

        rp = subprocess.run(
            ["java", "-cp", temp_dir, "Main"],
            capture_output=True, text=True,
        )

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
        shutil.rmtree(temp_dir, ignore_errors=True)
