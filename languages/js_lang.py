"""
JavaScript language adapter — Phase 3 update.

Bridge API available inside JS code (Node.js subprocess)
──────────────────────────────────────────────────────────
  poly_export(name, value)
      Publish a value back to the shared bridge.
      NOTE: We do NOT use export() — that conflicts with ES module syntax.

  get_global(name, fallback=null)
      Read any value previously published to the bridge.

  call_bridge(name, arg1, arg2, ...)
      Call a Python function registered with export_function().
      Uses the __POLY_CALL__ / __POLY_RET__ pipe protocol.
      Return value is typed: number, boolean, string, or null.

Shared globals are injected as:
    globalThis.key = value;
before user code runs.

Exports are collected via __POLY_EXPORT__<JSON> marker on stdout.
Function calls use the interactive pipe protocol in bridge/pipe_runner.py.
"""

import json
import re

from bridge.pipe_runner import run_interactive

EXPORT_MARKER = "__POLY_EXPORT__"
RET_MARKER    = "__POLY_RET__|"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_exports(code: str) -> str:
    """Rewrite bare  export(...)  to  poly_export(...)  to avoid ES-module clash."""
    return re.sub(r"(?<![.\w])export\s*\(", "poly_export(", code)


def _strip_hash_comments(code: str) -> str:
    """Remove lines starting with # (Python comments invalid in JS)."""
    lines = []
    for line in code.splitlines():
        if line.strip().startswith('#'):
            lines.append('')
        else:
            lines.append(line)
    return '\n'.join(lines)


def _parse_export_line(line: str):
    """
    Parse a __POLY_EXPORT__<JSON> line.
    Returns a dict of exports, or None if the line is not an export marker.
    """
    stripped = line.strip()
    if not stripped.startswith(EXPORT_MARKER):
        return None
    try:
        data = json.loads(stripped[len(EXPORT_MARKER):])
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None


# ── JS prelude (injected before user code) ────────────────────────────────────

_CALL_BRIDGE_JS = """\
globalThis._poly_read_ret = function() {
    // Read one __POLY_RET__ line synchronously from stdin
    var _fs  = require("fs");
    var _buf = Buffer.alloc(1);
    var _line = "";
    while (true) {
        var _n = _fs.readSync(0, _buf, 0, 1, null);
        if (_n === 0) break;
        var _ch = String.fromCharCode(_buf[0]);
        if (_ch === "\\n") break;
        _line += _ch;
    }
    _line = _line.replace(/\\r$/, "");

    var _RET = "__POLY_RET__|";
    if (!_line.startsWith(_RET)) return null;
    var _rest = _line.slice(_RET.length);
    var _idx  = _rest.indexOf("|");
    if (_idx < 0) return null;
    var _t = _rest.slice(0, _idx);
    var _v = _rest.slice(_idx + 1);

    if (_t === "int")   return parseInt(_v, 10);
    if (_t === "float") return parseFloat(_v);
    if (_t === "bool")  return _v === "true";
    if (_t === "null")  return null;
    // str — unescape
    return _v.replace(/\\\\n/g, "\\n")
             .replace(/\\\\r/g, "\\r")
             .replace(/\\\\\\\\/g, "\\\\");
};

globalThis.call_bridge = function() {
    var _name = arguments[0];
    var _args = Array.prototype.slice.call(arguments, 1);
    process.stdout.write(
        "__POLY_CALL__|" + _name + "|" + JSON.stringify(_args) + "\\n"
    );
    return globalThis._poly_read_ret();
};

// Milestone 3: register a JS function so Python can call it later.
// We wrap the source in  var __stub_fn = (<source>);  so any function
// type (named declaration, arrow, anonymous expression) is callable
// as  __stub_fn.apply(null, args)  in the stub invoker.
globalThis.poly_export_function = function(name, fn, return_type) {
    var _src     = fn.toString();
    var _wrapped = "var __stub_fn = (" + _src + ");";
    var _ret     = return_type || "auto";
    process.stdout.write(
        "__POLY_REGISTER__|" + name + "|js|" + _ret + "|" +
        JSON.stringify(_wrapped) + "\\n"
    );
};
"""


# ── Runner ────────────────────────────────────────────────────────────────────

def run(code: str, context) -> dict:
    code = _normalize_exports(code)
    code = _strip_hash_comments(code)

    # ── Inject shared globals into globalThis ─────────────────────────────
    global_lines: list[str] = []
    for key, value in context.all().items():
        if key.startswith("__") or callable(value):
            continue
        try:
            global_lines.append(
                f"globalThis[{json.dumps(key)}] = {json.dumps(value)};"
            )
        except (TypeError, ValueError):
            pass

    # ── Inject class schemas (Phase 3D) ───────────────────────────────────
    for cname, cfields in context.bridge.registry.class_schemas.items():
        args = ", ".join(cfields.keys())
        assigns = "\n".join(f"        this.{f} = {f};" for f in cfields.keys())
        cls_code = f"class {cname} {{\n    constructor({args}) {{\n{assigns}\n    }}\n}}\nglobalThis.{cname} = {cname};"
        global_lines.append(cls_code)

    # ── Bridge prelude ────────────────────────────────────────────────────
    prelude = f"""\
const __poly_exports = {{}};

globalThis.poly_export = function(name, value) {{
    __poly_exports[name] = value;
}};

globalThis.get_global = function(name, fallback) {{
    if (fallback === undefined) {{ fallback = null; }}
    const v = globalThis[name];
    if (v === undefined) return fallback;
    if (v && typeof v === "object" && typeof v.__handle__ === "number") {{
        return new Proxy(v, {{
            get: function(target, prop) {{
                if (prop in target) return target[prop];
                if (typeof prop === "string") {{
                    return function() {{
                        var _args = Array.prototype.slice.call(arguments);
                        process.stdout.write(
                            "__POLY_METHOD__|" + target.__handle__ + "|" + prop + "|" + JSON.stringify(_args) + "\\n"
                        );
                        return globalThis._poly_read_ret();
                    }};
                }}
            }}
        }});
    }}
    return v;
}};

{_CALL_BRIDGE_JS}
"""

    # ── Assemble full JS ──────────────────────────────────────────────────
    full_js = (
        "\n".join(global_lines)
        + "\n"
        + prelude
        + "\n"
        + code
        + f'\nprocess.stdout.write("{EXPORT_MARKER}" + JSON.stringify(__poly_exports) + "\\n");\n'
    )

    return run_interactive(
        ["node", "-e", full_js],
        context,
        _parse_export_line,
    )
