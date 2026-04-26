"""
runner.py — Generic subprocess runner for all PLF compiled/interpreted languages.

How it works
────────────
1.  Look up the adapter config from adapters.ADAPTERS.
2.  Read the native bridge-glue template file.
3.  Pre-process user code (JS comment stripping, export() renaming, etc.).
4.  Assemble the full source:
      globals_block  +  bridge_glue_template  +  class_schemas  +  user_code
    For Java: delegate to adapter.wrap_source() which handles class injection.
5.  Write to a temp file, compile if needed, run interactively via pipe_runner.
6.  Clean up the temp directory.

The JS case is special: no temp file is written — the assembled script is
passed directly to  node -e  via the command line.

All four languages share ONE run() entry point here.
"""

import os
import shutil
import subprocess
import tempfile

from bridge.protocol import run_subprocess
from .adapters import ADAPTERS


def run(lang: str, code: str, context) -> tuple:
    """
    Execute one polyglot block for the given language.

    Parameters
    ----------
    lang    : e.g. 'c', 'cpp', 'javascript', 'java'
    code    : raw user source code from the .poly block
    context : shared Context object

    Returns
    -------
    (exports_dict, stub_return_value)
    """
    cfg = ADAPTERS[lang]

    # ── 1. Pre-process user code if required (JS: strip # comments, rewrite export) ──
    if cfg["preprocess"]:
        code = cfg["preprocess"](code)

    # ── 2. Inject shared globals (always a string; may be empty) ──────────────────
    globals_block = cfg["inject_globals"](context) if cfg["inject_globals"] else ""

    # ── 3. Inject class schemas (None means inject_globals already handled it) ────
    classes_block = ""
    if cfg["inject_classes"]:
        classes_block = cfg["inject_classes"](context)

    # ── 4. Read bridge-glue template ───────────────────────────────────────────────
    with open(cfg["template"], encoding="utf-8") as f:
        bridge_glue = f.read()

    # ── 5. JavaScript — inline via node -e, no temp file ──────────────────────────
    EXPORT_MARKER = "__POLY_EXPORT__"
    if lang == "javascript":
        full_js = (
            globals_block + "\n"
            + bridge_glue + "\n"
            + code + "\n"
            + f'process.stdout.write("{EXPORT_MARKER}" + JSON.stringify(__poly_exports) + "\\n");\n'
        )
        return run_subprocess(["node", "-e", full_js], context, cfg["parse_export"])

    # ── 6. Compiled/JAR-run languages — write to OS temp dir ─────────────────
    # tempfile.mkdtemp() places the folder in C:\Users\...\AppData\Local\Temp\
    # so the project folder stays completely clean during compilation.
    build_dir = tempfile.mkdtemp(prefix=f"plf_{lang}_")

    try:
        # For Java the filename must be Main.java
        if lang == "java":
            src_name = "Main.java"
        else:
            src_name = f"main{cfg['suffix']}"
        src_path = os.path.join(build_dir, src_name)

        # ── Assemble source ────────────────────────────────────────────────────────
        if cfg["wrap_source"]:
            # Java: wrap_source builds the complete class around the code
            bridge_members = globals_block + "\n" + bridge_glue
            full_source = cfg["wrap_source"](code, bridge_members, context)
        else:
            # C / C++: globals → include/header → class schemas → user code
            full_source = (
                globals_block + "\n"
                + bridge_glue + "\n"
                + classes_block + "\n"
                + code
            )

        with open(src_path, "w", encoding="utf-8") as f:
            f.write(full_source)

        # ── Compile ────────────────────────────────────────────────────────────────
        if cfg["compile"]:
            out_path = os.path.join(build_dir, "main.exe")
            compile_cmd = cfg["compile"](src_path, out_path)
            cp = subprocess.run(compile_cmd, capture_output=True, text=True)
            if cp.returncode != 0:
                print(f"[{lang.upper()}] Compilation error:")
                print(cp.stderr.strip())
                return {}, None
        else:
            out_path = src_path   # Interpreted — run the source directly

        # ── Run ────────────────────────────────────────────────────────────────────
        run_cmd = cfg["run_cmd"](out_path, build_dir)
        return run_subprocess(run_cmd, context, cfg["parse_export"])

    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
