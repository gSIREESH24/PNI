"""
Bidirectional stdin/stdout pipe protocol for cross-language function calls.

Protocol
────────
Subprocess → Python  (subprocess writes to its stdout):
    __POLY_CALL__|<name>|<json_array_of_args>
    __POLY_EXPORT__ ...   (language-specific export markers, handled by caller)
    <anything else>       printed to host stdout

Python → Subprocess  (Python writes to subprocess stdin):
    __POLY_RET__|<type>|<value>
    where type ∈ { int, float, bool, str, null }

Why stdin/stdout?
    No external dependencies, works on all platforms, same pattern as
    the existing __POLY_EXPORT__ marker system.
"""

import json
import subprocess
import threading

CALL_MARKER     = "__POLY_CALL__|"
RET_MARKER      = "__POLY_RET__|"
REGISTER_MARKER = "__POLY_REGISTER__|"
METHOD_MARKER   = "__POLY_METHOD__|"


# ── Result encoder ────────────────────────────────────────────────────────────

def _encode_result(result) -> str:
    """Encode a Python value as a __POLY_RET__ line to write to subprocess stdin."""
    if result is None:
        return f"{RET_MARKER}null|null\n"
    if isinstance(result, bool):          # must come before int check
        return f"{RET_MARKER}bool|{'true' if result else 'false'}\n"
    if isinstance(result, int):
        return f"{RET_MARKER}int|{result}\n"
    if isinstance(result, float):
        return f"{RET_MARKER}float|{result!r}\n"
    if isinstance(result, str):
        safe = (result
                .replace("\\", "\\\\")
                .replace("\n", "\\n")
                .replace("\r", "\\r"))
        return f"{RET_MARKER}str|{safe}\n"
    # Fallback: stringify
    return f"{RET_MARKER}str|{str(result)}\n"

def _decode_ret(line: str):
    """Parse a __POLY_RET__|type|value line and return a Python value."""
    if not line.startswith(RET_MARKER):
        return None
    body = line[len(RET_MARKER):]
    idx  = body.find("|")
    if idx < 0:
        return None
    typ = body[:idx]
    val = body[idx + 1:].rstrip("\r\n")

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
    # str — unescape
    return (val.replace("\\n", "\n")
               .replace("\\r", "\r")
               .replace("\\\\", "\\"))


# ── Interactive runner ────────────────────────────────────────────────────────

def run_interactive(
    cmd: list,
    context,
    parse_export_line,
    cwd: str | None = None,
) -> dict:
    """
    Execute a subprocess using the bridge pipe protocol.

    Parameters
    ----------
    cmd              : Command + args list passed to Popen.
    context          : PolyBridge context — must expose .call(name, *args)
                       and .has_function(name).
    parse_export_line: Language-specific function.
                       Given one stdout line, returns a dict of new exports if
                       the line is an export marker, otherwise returns None.
    cwd              : Optional working directory for the subprocess.

    Returns
    -------
    (dict, Any): A tuple containing dict of all exports and a return value if execution emits a RET_MARKER (for stubs).
    """
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,       # line-buffered text mode
        cwd=cwd,
    )

    exports: dict       = {}
    stub_return_value   = None
    stderr_lines: list  = []

    # ── Drain stderr in a background thread to prevent pipe deadlocks ─────────
    def _drain_stderr():
        for ln in proc.stderr:
            stderr_lines.append(ln.rstrip())

    t = threading.Thread(target=_drain_stderr, daemon=True)
    t.start()

    # ── Main protocol loop ────────────────────────────────────────────────────
    try:
        for raw in proc.stdout:
            line = raw.rstrip("\n").rstrip("\r")

            # ── Bridge call request ──────────────────────────────────────────
            if line.startswith(CALL_MARKER):
                payload = line[len(CALL_MARKER):]
                sep     = payload.find("|")

                if sep < 0:
                    # Malformed — return null
                    proc.stdin.write(_encode_result(None))
                    proc.stdin.flush()
                    continue

                fn_name   = payload[:sep]
                args_json = payload[sep + 1:]

                result = None
                try:
                    args = json.loads(args_json)
                    if not isinstance(args, list):
                        args = [args]
                    result = context.call(fn_name, *args)
                except NameError as exc:
                    print(f"[Bridge] {exc}")
                except Exception as exc:
                    print(f"[Bridge] Error calling '{fn_name}': {exc}")

                proc.stdin.write(_encode_result(result))
                proc.stdin.flush()
                continue

            # ── Bridge method call (Phase 3E) ────────────────────────────────
            if line.startswith(METHOD_MARKER):
                payload = line[len(METHOD_MARKER):]
                parts = payload.split("|", 2)
                if len(parts) == 3:
                    try:
                        hnd       = int(parts[0])
                        meth_name = parts[1]
                        m_args    = json.loads(parts[2])
                        if not isinstance(m_args, list):
                            m_args = [m_args]
                        result = context.call_method(hnd, meth_name, *m_args)
                    except Exception as exc:
                        print(f"[Bridge] Error calling method '{parts[1]}': {exc}")
                        result = None
                else:
                    result = None

                proc.stdin.write(_encode_result(result))
                proc.stdin.flush()
                continue

            # ── Function stub registration (Milestone 3) ─────────────────────
            # Protocol: __POLY_REGISTER__|<name>|<language>|<return_type>|<json_source>
            if line.startswith(REGISTER_MARKER):
                payload = line[len(REGISTER_MARKER):]
                parts   = payload.split("|", 3)   # name | lang | ret_type | json_source
                if len(parts) == 4:
                    r_name, r_lang, r_ret, r_src_json = parts
                    try:
                        r_source = json.loads(r_src_json)
                        context.register_function_stub(r_name, r_lang, r_source, r_ret)
                        print(f"[Bridge] {r_lang} registered stub: '{r_name}' "
                              f"(return_type={r_ret})")
                    except Exception as exc:
                        print(f"[Bridge] Failed to register stub '{r_name}': {exc}")
                continue

            # ── Export marker ────────────────────────────────────────────────
            parsed = parse_export_line(line)
            if parsed is not None:
                exports.update(parsed)
                continue

            # ── Return marker (Stubs) ────────────────────────────────────────
            if line.startswith(RET_MARKER):
                stub_return_value = _decode_ret(line)
                continue

            # ── Normal output ────────────────────────────────────────────────
            print(line)

    except BrokenPipeError:
        pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait()
        t.join(timeout=2)

    if stderr_lines:
        print("\n".join(stderr_lines))

    return exports, stub_return_value
