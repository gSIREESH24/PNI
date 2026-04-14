"""
JavaScript language adapter — Milestone B.

Bridge API available inside JS code (Node.js subprocess)
──────────────────────────────────────────────────────────
  poly_export(name, value)
      Publish a value back to the shared bridge.
      NOTE: We do NOT use export() — that conflicts with ES module syntax.

  get_global(name, fallback=null)
      Read any value previously published to the bridge.

Shared globals are injected as:
    globalThis.key = value;
before user code runs. If a key is a valid JS identifier it can be
used directly (e.g.  let y = x * 2;  where x came from global {}).

All exports are sent as a single JSON object on the last stdout line
prefixed with __POLY_EXPORT__, which the adapter reads back.
"""

import json
import re
import subprocess

EXPORT_MARKER = "__POLY_EXPORT__"


def _normalize_exports(code: str) -> str:
    """Rewrite bare  export(...)  to  poly_export(...)  to avoid ES-module clash."""
    return re.sub(r"(?<![.\w])export\s*\(", "poly_export(", code)


def _strip_hash_comments(code: str) -> str:
    """Remove lines starting with # (Python comments invalid in JS)."""
    lines = []
    for line in code.splitlines():
        if line.strip().startswith('#'):
            lines.append('')   # keep line numbers intact
        else:
            lines.append(line)
    return '\n'.join(lines)


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
            pass   # skip values that aren't JSON-serialisable

    # ── Bridge prelude ────────────────────────────────────────────────────
    prelude = f"""\
const __poly_exports = {{}};

globalThis.poly_export = function(name, value) {{
    __poly_exports[name] = value;
}};

globalThis.get_global = function(name, fallback) {{
    if (fallback === undefined) {{ fallback = null; }}
    const v = globalThis[name];
    return (v !== undefined) ? v : fallback;
}};
"""

    # ── Assemble full JS to run ───────────────────────────────────────────
    full_js = (
        "\n".join(global_lines)
        + "\n"
        + prelude
        + "\n"
        + code
        + f'\nconsole.log("{EXPORT_MARKER}" + JSON.stringify(__poly_exports));\n'
    )

    result = subprocess.run(
        ["node", "-e", full_js],
        capture_output=True,
        text=True,
    )

    # Print non-marker lines to host stdout
    for line in result.stdout.splitlines():
        if not line.startswith(EXPORT_MARKER):
            print(line)
    if result.stderr:
        print(result.stderr.rstrip())

    # ── Parse exports from the marker line ───────────────────────────────
    exports: dict = {}
    for line in reversed(result.stdout.splitlines()):
        stripped = line.strip()
        if stripped.startswith(EXPORT_MARKER):
            try:
                exports = json.loads(stripped[len(EXPORT_MARKER):])
            except json.JSONDecodeError:
                pass
            break

    return exports
