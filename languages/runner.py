import os
import shutil
import subprocess
import tempfile

from bridge.protocol import run_subprocess
from .adapters import ADAPTERS


def run(lang: str, code: str, context) -> tuple:
    cfg = ADAPTERS[lang]

    if cfg["preprocess"]:
        code = cfg["preprocess"](code)

    globals_block = cfg["inject_globals"](context) if cfg["inject_globals"] else ""

    classes_block = ""
    if cfg["inject_classes"]:
        classes_block = cfg["inject_classes"](context)

    with open(cfg["template"], encoding="utf-8") as f:
        bridge_glue = f.read()

    EXPORT_MARKER = "__POLY_EXPORT__"
    if lang == "javascript":
        full_js = (
            globals_block + "\n"
            + bridge_glue + "\n"
            + code + "\n"
            + f'process.stdout.write("{EXPORT_MARKER}" + JSON.stringify(__poly_exports) + "\\n");\n'
        )
        return run_subprocess(["node", "-e", full_js], context, cfg["parse_export"])

    build_dir = tempfile.mkdtemp(prefix=f"plf_{lang}_")

    try:
        if lang == "java":
            src_name = "Main.java"
        else:
            src_name = f"main{cfg['suffix']}"
        src_path = os.path.join(build_dir, src_name)

        if cfg["wrap_source"]:
            bridge_members = globals_block + "\n" + bridge_glue
            full_source = cfg["wrap_source"](code, bridge_members, context)
        else:
            full_source = (
                globals_block + "\n"
                + bridge_glue + "\n"
                + classes_block + "\n"
                + code
            )

        with open(src_path, "w", encoding="utf-8") as f:
            f.write(full_source)

        if cfg["compile"]:
            out_path = os.path.join(build_dir, "main.exe")
            compile_cmd = cfg["compile"](src_path, out_path)
            cp = subprocess.run(compile_cmd, capture_output=True, text=True)
            if cp.returncode != 0:
                print(f"[{lang.upper()}] Compilation error:")
                print(cp.stderr.strip())
                return {}, None
        else:
            out_path = src_path

        run_cmd = cfg["run_cmd"](out_path, build_dir)
        return run_subprocess(run_cmd, context, cfg["parse_export"])

    finally:
        shutil.rmtree(build_dir, ignore_errors=True)
