import json
import subprocess
import threading


CALL_MARKER     = "__POLY_CALL__|"
RETURN_MARKER   = "__POLY_RET__|"
REGISTER_MARKER = "__POLY_REGISTER__|"
METHOD_MARKER   = "__POLY_METHOD__|"


def encode_return(value) -> str:
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


def run_subprocess(cmd: list, context, parse_export_line, cwd: str | None = None) -> tuple:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1, cwd=cwd,
    )

    exports:     dict = {}
    stub_return       = None
    stderr_lines: list = []

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

            elif (parsed := parse_export_line(line)) is not None:
                exports.update(parsed)

            elif line.startswith(RETURN_MARKER):
                stub_return = decode_return(line)

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
