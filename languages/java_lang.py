"""
Java language adapter — Phase 3 update.

Bridge API available inside Java code
───────────────────────────────────────
  export_value(String name, <type> value)
      Overloaded static method supporting: int, long, double, boolean, String, Object.
      Prints a __POLY_EXPORT__ marker to stdout.

  get_global(String name)
      Returns the bridge value stored under that name as an Object, or null.

  call_bridge(String name, Object... args)  → Object
      Call a Python function registered with export_function().
      Returns a typed Java value: Long, Double, Boolean, String, or null.
      Example:  Object r = call_bridge("square", 9);
                long  v = ((Long) call_bridge("square", 9));

Shared globals are injected as static final fields inside the Main class.
stdout is flushed explicitly; stdin is read via a static BufferedReader.

Function calls use the interactive pipe protocol in bridge/pipe_runner.py.

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

from bridge.pipe_runner import run_interactive

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

    # ── Inject class schemas (Phase 3D) ───────────────────────────────────
    JAVA_TYPE_MAP = {
        "int": "long",
        "float": "double",
        "bool": "boolean",
        "str": "String"
    }
    class_decls: list[str] = []
    if context is not None:
        for cname, cfields in context.bridge.registry.class_schemas.items():
            lines = [f"    public static class {cname} {{"]
            # Fields
            for f, t in cfields.items():
                lines.append(f"        public {JAVA_TYPE_MAP.get(t, 'long')} {f};")
            
            # Constructor
            args_j = ", ".join(f"{JAVA_TYPE_MAP.get(t, 'long')} {f}" for f, t in cfields.items())
            lines.append(f"        public {cname}({args_j}) {{")
            for f in cfields.keys():
                lines.append(f"            this.{f} = {f};")
            lines.append("        }")
            lines.append("    }")
            
            # export_value overload
            lines.append(f"    public static void export_value(String name, {cname} obj) {{")
            lines.append(f"        StringBuilder sb = new StringBuilder();")
            lines.append(f"        sb.append(\"{{ \");")
            for i, (f, t) in enumerate(cfields.items()):
                comma = "," if i < len(cfields)-1 else ""
                lines.append(f"        sb.append(\"\\\"{f}\\\":\");")
                if t == "str":
                    lines.append(f"        sb.append(\"\\\"\").append(obj.{f} == null ? \"\" : obj.{f}.replace(\"\\\\\\\\\", \"\\\\\\\\\\\\\\\\\").replace(\"\\\"\", \"\\\\\\\\\\\"\").replace(\"\\\\n\", \"\\\\\\\\n\").replace(\"\\\\r\", \"\\\\\\\\r\")).append(\"\\\"\");")
                else:
                    lines.append(f"        sb.append(obj.{f});")
                if comma:
                    lines.append(f"        sb.append(\"{comma}\");")
            lines.append(f"        sb.append(\" }}\");")
            lines.append(f"        System.out.println(\"__POLY_EXPORT__\" + name + \"|json|\" + sb.toString());")
            lines.append(f"        System.out.flush();")
            lines.append(f"    }}")
            class_decls.append("\n".join(lines))
    
    classes_block = "\n".join(class_decls)

    return f"""\
    /* ── PolyBridge: class schemas ── */
{classes_block}

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
        System.out.flush();
    }}
    public static void export_value(String name, long value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|int|" + value);
        System.out.flush();
    }}
    public static void export_value(String name, double value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|double|" + value);
        System.out.flush();
    }}
    public static void export_value(String name, boolean value) {{
        System.out.println("{EXPORT_PREFIX}" + name + "|bool|" + value);
        System.out.flush();
    }}
    public static void export_value(String name, String value) {{
        String safe = (value == null) ? "" : value
            .replace("\\\\", "\\\\\\\\")
            .replace("|",    "\\\\|")
            .replace("\\n",  "\\\\n")
            .replace("\\r",  "\\\\r");
        System.out.println("{EXPORT_PREFIX}" + name + "|string|" + safe);
        System.out.flush();
    }}
    public static void export_value(String name, Object value) {{
        export_value(name, value == null ? "null" : String.valueOf(value));
    }}

    /* ── PolyBridge: call_bridge ── */
    private static final java.io.BufferedReader __bridge_stdin =
        new java.io.BufferedReader(new java.io.InputStreamReader(System.in));

    private static Object _parse_ret(String line) {{
        if (line == null || !line.startsWith("__POLY_RET__|")) return null;
        String rest = line.substring("__POLY_RET__|".length());
        int idx = rest.indexOf('|');
        if (idx < 0) return null;
        String type = rest.substring(0, idx);
        String val  = rest.substring(idx + 1);
        switch (type) {{
            case "int":   return Long.parseLong(val.trim());
            case "float": return Double.parseDouble(val.trim());
            case "bool":  return val.trim().equals("true");
            case "null":  return null;
            default:      return val
                .replace("\\\\n", "\\n")
                .replace("\\\\r", "\\r")
                .replace("\\\\\\\\", "\\\\");
        }}
    }}

    private static String _format_args(Object... args) {{
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < args.length; i++) {{
            if (i > 0) sb.append(",");
            Object a = args[i];
            if (a instanceof String) {{
                sb.append("\\"")
                  .append(((String) a).replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\""))
                  .append("\\"");
            }} else if (a == null) {{
                sb.append("null");
            }} else {{
                sb.append(a);
            }}
        }}
        sb.append("]");
        return sb.toString();
    }}

    public static Object call_bridge(String name, Object... args) {{
        System.out.println("__POLY_CALL__|" + name + "|" + _format_args(args));
        System.out.flush();
        try {{
            return _parse_ret(__bridge_stdin.readLine());
        }} catch (Exception e) {{
            return null;
        }}
    }}

    /* ── Phase 3E: Method Proxies ── */
    public static Object call_method(long handle, String method, Object... args) {{
        System.out.println("__POLY_METHOD__|" + handle + "|" + method + "|" + _format_args(args));
        System.out.flush();
        try {{
            return _parse_ret(__bridge_stdin.readLine());
        }} catch (Exception e) {{
            return null;
        }}
    }}

    /* ── Milestone 3: export_bridge_function ── */
    public static void export_bridge_function(String name, String source, String returnType) {{
        String safeSource = source
            .replace("\\\\", "\\\\\\\\")
            .replace("\\"", "\\\\\\"")
            .replace("\\n", "\\\\n")
            .replace("\\r", "\\\\r")
            .replace("\\t", "\\\\t");
        System.out.println("__POLY_REGISTER__|" + name + "|java|" + returnType + "|\\"" + safeSource + "\\"");
        System.out.flush();
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

def run(text: str, context=None) -> dict:
    bridge_members = _build_bridge_members(context)
    java_source    = _wrap(text, bridge_members)

    temp_dir = os.path.join(os.getcwd(), f"_poly_java_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)

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

        return run_interactive(
            ["java", "-cp", temp_dir, "Main"],
            context,
            _parse_export_line,
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
