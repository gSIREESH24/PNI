import json
import os
import re
import textwrap

_HERE = os.path.dirname(__file__)

EXPORT_PREFIX = "__POLY_EXPORT__"

def _parse_export_standard(line: str):
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
        return {name: raw.replace("\\|", "|").replace("\\n", "\n")
                         .replace("\\r", "\r").replace("\\\\", "\\")}
    if type_name == "json":
        try:    return {name: json.loads(raw)}
        except ValueError: return None
    return {name: raw}


_JS_EXPORT_MARKER = "__POLY_EXPORT__"

def _parse_export_js(line: str):
    stripped = line.strip()
    if not stripped.startswith(_JS_EXPORT_MARKER):
        return None
    try:
        data = json.loads(stripped[len(_JS_EXPORT_MARKER):])
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _c_literal(value):
    if isinstance(value, bool): return ("1" if value else "0", "int")
    if value is None:           return ("0", "int")
    if isinstance(value, int):  return (str(value), "long long")
    if isinstance(value, float): return (repr(value), "double")
    if isinstance(value, str):
        esc = value.replace("\\", "\\\\").replace("\n","\\n").replace("\r","\\r").replace('"','\\"').replace("|","\\|")
        return (f'"{esc}"', "char *")
    return None

def _inject_c_globals(context) -> str:
    lines = []
    if context is None:
        return ""
    for key, value in context.all().items():
        if key.startswith("__") or callable(value):
            continue
        result = _c_literal(value)
        if result is None:
            continue
        literal, ctype = result
        lines.append(f"static const {ctype} {key} = {literal};")
    return "\n".join(lines)


def _inject_c_classes(context) -> str:
    if context is None:
        return ""
    C_TYPE = {"int": "long long", "float": "double", "bool": "bool", "str": "const char *"}
    parts = []
    for cname, cfields in context.bridge.registry.class_schemas.items():
        fields_c = " ".join(f"{C_TYPE.get(t,'long long')} {f};" for f, t in cfields.items())
        parts.append(f"typedef struct {{ {fields_c} }} {cname};")
        macro = [f"#define export_value_{cname}(name, obj) do {{ \\",
                 f'    printf("__POLY_EXPORT__%s|json|{{ ", name); \\']
        for i, (f, t) in enumerate(cfields.items()):
            comma = "," if i < len(cfields) - 1 else ""
            macro.append(f'    printf("\\"{f}\\":"); \\')
            if t == "int":
                macro.append(f'    printf("%lld{comma}", obj.{f}); \\')
            elif t == "float":
                macro.append(f'    printf("%f{comma}", obj.{f}); \\')
            elif t == "bool":
                macro.append(f'    printf("%s{comma}", obj.{f} ? "true" : "false"); \\')
            elif t == "str":
                macro.append(f'    _poly_json_str(obj.{f}); printf("{comma}"); \\')
        macro.append('    printf(" }\\n"); \\')
        macro.append('    fflush(stdout); \\')
        macro.append("} while(0)")
        parts.append("\n".join(macro))
    return "\n".join(parts)


def _inject_cpp_globals(context) -> str:
    if context is None:
        return ""
    lines = []
    for key, value in context.all().items():
        if key.startswith("__") or callable(value):
            continue
        result = _c_literal(value)
        if result is None:
            continue
        literal, ctype = result
        lines.append(f"static const {ctype} {key} = {literal};")
    return "\n".join(lines)


def _inject_cpp_classes(context) -> str:
    if context is None:
        return ""
    CPP_TYPE = {"int": "long long", "float": "double", "bool": "bool", "str": "std::string"}
    parts = []
    for cname, cfields in context.bridge.registry.class_schemas.items():
        fields = " ".join(f"{CPP_TYPE.get(t,'long long')} {f};" for f, t in cfields.items())
        parts.append(f"struct {cname} {{\n    {fields}\n}};")
        func = [f"namespace polybridge {{",
                f"inline void export_value(const std::string& name, const {cname}& obj) {{",
                f'    std::cout << "__POLY_EXPORT__" << name << "|json|{{ ";']
        for i, (f, t) in enumerate(cfields.items()):
            comma = "," if i < len(cfields) - 1 else ""
            func.append(f'    std::cout << "\\"{f}\\":";')
            if t in ("int", "float"):
                func.append(f'    std::cout << obj.{f} << "{comma}";')
            elif t == "bool":
                func.append(f'    std::cout << (obj.{f} ? "true" : "false") << "{comma}";')
            elif t == "str":
                func.append(f'    _poly_json_str(obj.{f}.c_str()); std::cout << "{comma}";')
        func.append('    std::cout << " }\\n";')
        func.append('    std::cout.flush();')
        func.append("}")
        func.append("}")
        parts.append("\n".join(func))
    return "\n".join(parts)


def _inject_js_globals(context) -> str:
    if context is None:
        return ""
    lines = []
    for key, value in context.all().items():
        if key.startswith("__") or callable(value):
            continue
        try:
            lines.append(f"globalThis[{json.dumps(key)}] = {json.dumps(value)};")
        except (TypeError, ValueError):
            pass
    for cname, cfields in context.bridge.registry.class_schemas.items():
        args    = ", ".join(cfields.keys())
        assigns = "\n".join(f"        this.{f} = {f};" for f in cfields.keys())
        lines.append(
            f"class {cname} {{\n    constructor({args}) {{\n{assigns}\n    }}\n}}\n"
            f"globalThis.{cname} = {cname};"
        )
    return "\n".join(lines)


def _inject_java_members(context) -> str:
    if context is None:
        return ""

    JAVA_TYPE = {"int": "long", "float": "double", "bool": "boolean", "str": "String"}

    def _escape_java(s):
        return (s.replace("\\", "\\\\").replace("\n","\\n").replace("\r","\\r")
                  .replace('"', '\\"').replace("|","\\|"))

    field_lines, map_puts = [], []
    for key, value in context.all().items():
        if key.startswith("__") or callable(value):
            continue
        if isinstance(value, bool):
            field_lines.append(f"    static final boolean {key} = {str(value).lower()};")
            map_puts.append(f'        __globals.put("{key}", {key});')
        elif isinstance(value, int):
            field_lines.append(f"    static final long {key} = {value}L;")
            map_puts.append(f'        __globals.put("{key}", {key});')
        elif isinstance(value, float):
            field_lines.append(f"    static final double {key} = {repr(value)};")
            map_puts.append(f'        __globals.put("{key}", {key});')
        elif isinstance(value, str):
            field_lines.append(f'    static final String {key} = "{_escape_java(value)}";')
            map_puts.append(f'        __globals.put("{key}", {key});')

    class_decls = []
    for cname, cfields in context.bridge.registry.class_schemas.items():
        lines = [f"    public static class {cname} {{"]
        for f, t in cfields.items():
            lines.append(f"        public {JAVA_TYPE.get(t,'long')} {f};")
        args_j = ", ".join(f"{JAVA_TYPE.get(t,'long')} {f}" for f, t in cfields.items())
        lines.append(f"        public {cname}({args_j}) {{")
        for f in cfields.keys():
            lines.append(f"            this.{f} = {f};")
        lines.append("        }")
        lines.append("    }")
        lines.append(f"    public static void export_value(String name, {cname} obj) {{")
        lines.append( "        StringBuilder sb = new StringBuilder();")
        lines.append( '        sb.append("{ ");')
        for i, (f, t) in enumerate(cfields.items()):
            comma = "," if i < len(cfields) - 1 else ""
            lines.append(f'        sb.append("\\"{f}\\":");')
            if t == "str":
                lines.append(f'        sb.append("\\"").append(obj.{f} == null ? "" : '
                             f'obj.{f}.replace("\\\\", "\\\\\\\\").replace("\\"", "\\\\\\"")).append("\\"");')
            else:
                lines.append(f"        sb.append(obj.{f});")
            if comma:
                lines.append(f'        sb.append("{comma}");')
        lines.append('        sb.append(" }");')
        lines.append(f'        System.out.println("__POLY_EXPORT__" + name + "|json|" + sb.toString());')
        lines.append( "        System.out.flush();")
        lines.append( "    }")
        class_decls.append("\n".join(lines))

    puts_block = "\n".join(map_puts) if map_puts else "        "
    return (
        "\n".join(class_decls) + "\n" +
        "\n".join(field_lines) + "\n" +
        "    private static final java.util.Map<String,Object> __globals = new java.util.HashMap<>();\n"
        "    static {\n" + puts_block + "\n    }\n"
        "    public static Object get_global(String name) { return __globals.get(name); }\n"
    )


def _wrap_java(code: str, bridge_members: str, _context) -> str:
    stripped = textwrap.dedent(code).strip()
    m = re.search(r"(class\s+Main\s*\{)", stripped)
    if m:
        pos = m.end()
        return stripped[:pos] + "\n" + bridge_members + stripped[pos:]
    body = textwrap.indent(stripped, " " * 8)
    return (
        "public class Main {\n"
        + bridge_members + "\n"
        + "    public static void main(String[] args) {\n"
        + body + "\n"
        + "    }\n"
        + "}\n"
    )


def _normalize_js_exports(code: str) -> str:
    return re.sub(r"(?<![.\w])export\s*\(", "poly_export(", code)


def _strip_js_hash_comments(code: str) -> str:
    return code


def _tpl(filename: str) -> str:
    return os.path.join(_HERE, "templates", filename)


ADAPTERS = {
    "c": {
        "template":       _tpl("c_bridge.h"),
        "suffix":         ".c",
        "compile":        lambda src, out: ["gcc", "-std=c11", src, "-o", out],
        "run_cmd":        lambda out, _bd: [out],
        "inject_globals": _inject_c_globals,
        "inject_classes": _inject_c_classes,
        "parse_export":   _parse_export_standard,
        "wrap_source":    None,
        "preprocess":     None,
    },
    "cpp": {
        "template":       _tpl("cpp_bridge.hpp"),
        "suffix":         ".cpp",
        "compile":        lambda src, out: ["g++", "-std=c++17", src, "-o", out],
        "run_cmd":        lambda out, _bd: [out],
        "inject_globals": _inject_cpp_globals,
        "inject_classes": _inject_cpp_classes,
        "parse_export":   _parse_export_standard,
        "wrap_source":    None,
        "preprocess":     None,
    },
    "javascript": {
        "template":       _tpl("js_bridge.js"),
        "suffix":         ".js",
        "compile":        None,
        "run_cmd":        None,
        "inject_globals": _inject_js_globals,
        "inject_classes": None,
        "parse_export":   _parse_export_js,
        "wrap_source":    None,
        "preprocess":     lambda code: _normalize_js_exports(code),
    },
    "java": {
        "template":       _tpl("java_bridge.java"),
        "suffix":         ".java",
        "compile":        lambda src, _out: ["javac", "-encoding", "UTF-8", src],
        "run_cmd":        lambda _out, bd: ["java", "-cp", bd, "Main"],
        "inject_globals": _inject_java_members,
        "inject_classes": None,
        "parse_export":   _parse_export_standard,
        "wrap_source":    _wrap_java,
        "preprocess":     None,
    },
}
