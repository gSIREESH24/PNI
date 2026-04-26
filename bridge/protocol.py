"""
protocol.py — Bidirectional stdin/stdout pipe protocol for cross-language calls.

Wire format
───────────
Subprocess → Python (written to subprocess stdout):
    __POLY_CALL__|<name>|<json_array_args>     — call a Python-registered function
    __POLY_METHOD__|<handle>|<method>|<json>   — call a method on a stored object
    __POLY_REGISTER__|<name>|<lang>|<ret>|<src>— register this function as a stub
    __POLY_EXPORT__...                         — language-specific export line

Python → Subprocess (written to subprocess stdin):
    __POLY_RET__|<type>|<value>                — typed return value
    where type ∈ { int, float, bool, str, null }
"""

import json
import subprocess
import threading


# ── Protocol marker constants ─────────────────────────────────────────────────

CALL_MARKER     = "__POLY_CALL__|"
RETURN_MARKER   = "__POLY_RET__|"
REGISTER_MARKER = "__POLY_REGISTER__|"
METHOD_MARKER   = "__POLY_METHOD__|"


# ── Return value codec ────────────────────────────────────────────────────────

def encode_return(value) -> str:
    """Encode a Python value into a __POLY_RET__ wire line."""
    if value is None:
        return f"{RETURN_MARKER}null|null\n"
    if isinstance(value, bool):
        return f"{RETURN_MARKER}bool|{'true' if value else 'false'}\n"
    if isinstance(value, int):
        return f"{RETURN_MARKER}int|{value}\n"
    if isinstance(value, float):
        return f"{RETURN_MARKER}float|{value!r}\n"
    if isinstance(value, str):
        safe = value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
        return f"{RETURN_MARKER}str|{safe}\n"
    return f"{RETURN_MARKER}str|{str(value)}\n"


def decode_return(line: str):
    """Parse a __POLY_RET__|type|value line back into a Python value."""
    if not line.startswith(RETURN_MARKER):
        return None
    body = line[len(RETURN_MARKER):]
    sep  = body.find("|")
    if sep < 0:
        return None
    typ, val = body[:sep], body[sep + 1:].rstrip("\r\n")

    if typ == "int":
        try:    return int(val)
        except ValueError: return None
    if typ == "float":
        try:    return float(val)
        except ValueError: return None
    if typ == "bool":
        return val.lower() == "true"
    if typ == "null":
        return None
    return val.replace("\\n", "\n").replace("\\r", "\r").replace("\\\\", "\\")


# ── Subprocess runner ─────────────────────────────────────────────────────────

def run_subprocess(cmd: list, context, parse_export_line, cwd: str | None = None) -> tuple:
    """
    Launch a subprocess and drive the bridge pipe protocol until it exits.

    Parameters
    ----------
    cmd              : Command + args for Popen.
    context          : Active Context — exposes .call(), .call_method(),
                       .register_function_stub().
    parse_export_line: Language-specific parser.
                       Returns {name: value} dict from an export line, or None.
    cwd              : Optional working directory.

    Returns
    -------
    (exports: dict, stub_return: Any)
        exports      — all values collected from export markers
        stub_return  — the last __POLY_RET__ value seen (used by stub calls)
    """
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, cwd=cwd,
    )

    exports:     dict = {}
    stub_return       = None
    stderr_lines: list = []

    # Drain stderr on a background thread to prevent pipe deadlocks.
    def _drain_stderr():
        for ln in proc.stderr:
            stderr_lines.append(ln.rstrip())

    drain = threading.Thread(target=_drain_stderr, daemon=True)
    drain.start()

    def _send(value):
        proc.stdin.write(encode_return(value))
        proc.stdin.flush()

    try:
        for raw in proc.stdout:
            line = raw.rstrip("\n").rstrip("\r")

            # ── Function call request ─────────────────────────────────────────
            if line.startswith(CALL_MARKER):
                payload = line[len(CALL_MARKER):]
                sep     = payload.find("|")
                if sep < 0:
                    _send(None)
                    continue
                fn_name, args_json = payload[:sep], payload[sep + 1:]
                result = None
                try:
                    args = json.loads(args_json)
                    result = context.call(fn_name, *(args if isinstance(args, list) else [args]))
                except NameError as exc:
                    print(f"[Bridge] {exc}")
                except Exception as exc:
                    print(f"[Bridge] Error calling '{fn_name}': {exc}")
                _send(result)

            # ── Object method call ────────────────────────────────────────────
            elif line.startswith(METHOD_MARKER):
                parts = line[len(METHOD_MARKER):].split("|", 2)
                result = None
                if len(parts) == 3:
                    try:
                        handle, method = int(parts[0]), parts[1]
                        m_args = json.loads(parts[2])
                        result = context.call_method(handle, method, *(m_args if isinstance(m_args, list) else [m_args]))
                    except Exception as exc:
                        print(f"[Bridge] Error calling method '{parts[1]}': {exc}")
                _send(result)

            # ── Function stub registration ────────────────────────────────────
            elif line.startswith(REGISTER_MARKER):
                parts = line[len(REGISTER_MARKER):].split("|", 3)
                if len(parts) == 4:
                    name, lang, ret_type, src_json = parts
                    try:
                        source = json.loads(src_json)
                        context.register_function_stub(name, lang, source, ret_type)
                        print(f"[Bridge] {lang} registered stub: '{name}' (return={ret_type})")
                    except Exception as exc:
                        print(f"[Bridge] Failed to register stub '{name}': {exc}")

            # ── Export line ───────────────────────────────────────────────────
            elif (parsed := parse_export_line(line)) is not None:
                exports.update(parsed)

            # ── Return value (stub calls) ─────────────────────────────────────
            elif line.startswith(RETURN_MARKER):
                stub_return = decode_return(line)

            # ── Normal program output ─────────────────────────────────────────
            else:
                print(line)

    except BrokenPipeError:
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()
        drain.join(timeout=2)

    if stderr_lines:
        print("\n".join(stderr_lines))

    return exports, stub_return
