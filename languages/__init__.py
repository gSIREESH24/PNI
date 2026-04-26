from .python_lang import run as python_run
from .runner      import run as _compiled_run

def _make_run(lang):
    def _run(code, context):
        return _compiled_run(lang, code, context)
    return _run

LANGUAGE_REGISTRY = {
    "python":     python_run,
    "javascript": _make_run("javascript"),
    "js":         _make_run("javascript"),
    "c":          _make_run("c"),
    "c++":        _make_run("cpp"),
    "cpp":        _make_run("cpp"),
    "java":       _make_run("java"),
}
