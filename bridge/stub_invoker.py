"""
stub_invoker.py — Milestone 3: re-invoke a subprocess function by its source.

When Python calls a function registered by JS / C / C++ / Java, we cannot
call it "live" (those processes already exited).  Instead we:
  1. Spin up a tiny one-shot subprocess that contains ONLY the registered
     function source + a small harness that calls it with the supplied args.
  2. Parse the result from a __POLY_RET__ line on stdout.
  3. Return the typed Python value.

Protocol on the mini subprocess stdout:
    __POLY_RET__|<type>|<value>
    where type ∈ { int, float, bool, str, null }

This is the same RET format used by pipe_runner for call responses,
so the same decoder can be reused.
"""

import json
import os
import shutil
import subprocess
import tempfile
import uuid

RET_MARKER = "__POLY_RET__|"


# ── Return-value decoder ──────────────────────────────────────────────────────

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


# ── Python-value → language-literal helpers ───────────────────────────────────

def _to_c_literal(v) -> str:
    if v is None:          return "0"
    if isinstance(v, bool): return "1" if v else "0"
    if isinstance(v, int):  return f"{v}LL"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = (v.replace("\\", "\\\\")
                .replace('"',  '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r"))
        return f'"{esc}"'
    return "0"

def _c_args(args: list) -> str:
    return ", ".join(_to_c_literal(a) for a in args)


def _to_java_literal(v) -> str:
    if v is None:          return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, int):  return f"{v}L"
    if isinstance(v, float): return repr(v)
    if isinstance(v, str):
        esc = (v.replace("\\", "\\\\")
                .replace('"',  '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r"))
        return f'"{esc}"'
    return "null"

def _java_args(args: list) -> str:
    return ", ".join(_to_java_literal(a) for a in args)


# ── Per-language invokers ─────────────────────────────────────────────────────

def _invoke_js(fn_name: str, source: str, args: list, return_type: str):
    """
    source is already wrapped as  var __stub_fn = (<original_source>);
    so we just call  __stub_fn.apply(null, args).
    """
    args_json = json.dumps(args)
    script = f"""\
{source}
(function() {{
  var __args = {args_json};
  var __r = __stub_fn.apply(null, __args);
  var __t = typeof __r;
  if (__r === null || __r === undefined) {{
    process.stdout.write("{RET_MARKER}null|null\\n");
  }} else if (__t === "boolean") {{
    process.stdout.write("{RET_MARKER}bool|" + __r + "\\n");
  }} else if (__t === "number") {{
    if (Number.isInteger(__r))
      process.stdout.write("{RET_MARKER}int|"   + __r + "\\n");
    else
      process.stdout.write("{RET_MARKER}float|" + __r + "\\n");
  }} else {{
    process.stdout.write("{RET_MARKER}str|" + String(__r) + "\\n");
  }}
}})();
"""
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=15)
    for line in r.stdout.splitlines():
        if line.startswith(RET_MARKER):
            return _decode_ret(line)
    if r.stderr:
        print(f"[Bridge/JS stub] {r.stderr.strip()}")
    return None


def _invoke_c(fn_name: str, source: str, args: list, return_type: str):
    rt = return_type or "int"
    args_c = _c_args(args)

    if rt == "float":
        call_expr = f"(double)({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}float|%.17g\\n", {call_expr});'
    elif rt == "bool":
        call_expr = f"({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}bool|%s\\n", {call_expr} ? "true" : "false");'
    elif rt == "str":
        call_expr = f"({fn_name}({args_c}))"
        print_stmt = f'{{ const char* __s = {call_expr}; printf("{RET_MARKER}str|%s\\n", __s ? __s : ""); }}'
    else:  # int / default
        call_expr = f"(long long)({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}int|%lld\\n", {call_expr});'

    c_src = f"""\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

{source}

int main(void) {{
    {print_stmt}
    return 0;
}}
"""
    build_dir = os.path.join(os.getcwd(), f"_stub_c_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    c_file = os.path.join(build_dir, "stub.c")
    exe    = os.path.join(build_dir, "stub.exe")
    try:
        with open(c_file, "w", encoding="utf-8") as f:
            f.write(c_src)
        cp = subprocess.run(["gcc", "-std=c11", c_file, "-o", exe],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"[Bridge/C stub] Compile error:\n{cp.stderr.strip()}")
            return None
        rp = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        for line in rp.stdout.splitlines():
            if line.startswith(RET_MARKER):
                return _decode_ret(line)
        if rp.stderr:
            print(f"[Bridge/C stub] {rp.stderr.strip()}")
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
    return None


def _invoke_cpp(fn_name: str, source: str, args: list, return_type: str):
    rt = return_type or "int"
    args_c = _c_args(args)   # C++ literals are the same as C literals here

    if rt == "float":
        call_expr  = f"(double)({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}float|%.17g\\n", {call_expr});'
    elif rt == "bool":
        call_expr  = f"({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}bool|%s\\n", {call_expr} ? "true" : "false");'
    elif rt == "str":
        call_expr  = f"({fn_name}({args_c}))"
        print_stmt = f'{{ auto __s = {call_expr}; printf("{RET_MARKER}str|%s\\n", __s.c_str()); }}'
    else:
        call_expr  = f"(long long)({fn_name}({args_c}))"
        print_stmt = f'printf("{RET_MARKER}int|%lld\\n", {call_expr});'

    cpp_src = f"""\
#include <iostream>
#include <string>
#include <cstdio>
#include <cstdlib>
#include <cstring>

{source}

int main() {{
    {print_stmt}
    return 0;
}}
"""
    build_dir = os.path.join(os.getcwd(), f"_stub_cpp_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    cpp_file = os.path.join(build_dir, "stub.cpp")
    exe      = os.path.join(build_dir, "stub.exe")
    try:
        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(cpp_src)
        cp = subprocess.run(["g++", "-std=c++17", cpp_file, "-o", exe],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"[Bridge/C++ stub] Compile error:\n{cp.stderr.strip()}")
            return None
        rp = subprocess.run([exe], capture_output=True, text=True, timeout=10)
        for line in rp.stdout.splitlines():
            if line.startswith(RET_MARKER):
                return _decode_ret(line)
        if rp.stderr:
            print(f"[Bridge/C++ stub] {rp.stderr.strip()}")
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
    return None


def _invoke_java(fn_name: str, source: str, args: list, return_type: str):
    rt = return_type or "int"
    args_j = _java_args(args)

    if rt == "float":
        call_expr  = f"(double)({fn_name}({args_j}))"
        print_stmt = f'System.out.println("{RET_MARKER}float|" + {call_expr});'
    elif rt == "bool":
        call_expr  = f"({fn_name}({args_j}))"
        print_stmt = f'System.out.println("{RET_MARKER}bool|" + ({call_expr} ? "true" : "false"));'
    elif rt == "str":
        call_expr  = f"String.valueOf({fn_name}({args_j}))"
        print_stmt = f'System.out.println("{RET_MARKER}str|" + {call_expr});'
    else:
        call_expr  = f"(long)({fn_name}({args_j}))"
        print_stmt = f'System.out.println("{RET_MARKER}int|" + {call_expr});'

    java_src = f"""\
public class __PolyStub {{
    {source}

    public static void main(java.lang.String[] __a) {{
        {print_stmt}
        System.out.flush();
    }}
}}
"""
    build_dir = os.path.join(os.getcwd(), f"_stub_java_{uuid.uuid4().hex}")
    os.makedirs(build_dir, exist_ok=True)
    java_file = os.path.join(build_dir, "__PolyStub.java")
    try:
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(java_src)
        cp = subprocess.run(["javac", "-encoding", "UTF-8", java_file],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"[Bridge/Java stub] Compile error:\n{cp.stderr.strip()}")
            return None
        rp = subprocess.run(["java", "-cp", build_dir, "__PolyStub"],
                            capture_output=True, text=True, timeout=15)
        for line in rp.stdout.splitlines():
            if line.startswith(RET_MARKER):
                return _decode_ret(line)
        if rp.stderr:
            print(f"[Bridge/Java stub] {rp.stderr.strip()}")
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
    return None


# ── Public entry point ────────────────────────────────────────────────────────

def invoke(fn_name: str, language: str, source: str, return_type: str, args: list):
    """
    Re-invoke a registered subprocess function by spinning up a one-shot
    mini-subprocess containing only the function source + a call harness.

    Parameters
    ----------
    fn_name     : registered function name
    language    : "js" | "c" | "cpp" | "java"
    source      : full source code string for the function
    return_type : "int" | "float" | "bool" | "str"  (hints for type-safe output)
    args        : Python list of arguments

    Returns
    -------
    Typed Python value (int, float, bool, str, or None).
    """
    lang = language.lower()
    if lang == "js":
        return _invoke_js(fn_name, source, args, return_type)
    if lang == "c":
        return _invoke_c(fn_name, source, args, return_type)
    if lang in ("cpp", "c++"):
        return _invoke_cpp(fn_name, source, args, return_type)
    if lang == "java":
        return _invoke_java(fn_name, source, args, return_type)
    raise ValueError(f"[Bridge] stub_invoker: unsupported language '{language}'")
