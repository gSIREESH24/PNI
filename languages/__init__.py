from .python_lang import run as python_run
from .js_lang     import run as js_run
from .c_lang      import run as c_run
from .cpp_lang    import run as cpp_run
from .java_lang   import run as java_run

LANGUAGE_REGISTRY = {
    "python":     python_run,
    "javascript": js_run,
    "js":         js_run,
    "c":          c_run,
    "c++":        cpp_run,
    "cpp":        cpp_run,
    "java":       java_run,
}
