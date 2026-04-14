"""
Phase-2 Polyglot Language Framework — Test Suite
=================================================

Milestones covered
─────────────────────────────────────────────────
  Milestone A  tests 01-04  Python → bridge → Python
  Milestone B  test  05     Python ↔ JavaScript
  Milestone C  tests 06-07  Python ↔ C / C++
  Milestone D  test  08     Python ↔ Java
  Milestone E  test  09     Full mixed sequential program
               test  10     Python-to-Python function call through bridge
"""

import unittest

from core.parser      import parse
from core.context     import Context
from core.interpreter import process_global
from languages        import LANGUAGE_REGISTRY


# ── Helper ────────────────────────────────────────────────────────────────────

def _run_source(test_case: unittest.TestCase, source: str) -> Context:
    """Parse source, execute every block in order, return final Context."""
    program = parse(source)
    context = Context()
    for block in program.blocks:
        if block.language == "global":
            process_global(block.code, context)
        else:
            runner = LANGUAGE_REGISTRY.get(block.language)
            test_case.assertIsNotNone(runner, f"No adapter for language: {block.language!r}")
            exports = runner(block.code, context)
            if isinstance(exports, dict):
                for k, v in exports.items():
                    context.set(k, v)
    return context


# ── Test Suite ────────────────────────────────────────────────────────────────

class TestPhase2(unittest.TestCase):

    # ══ Milestone A — global values + Python in-process ═══════════════════

    def test_01_global_variable_parsing(self):
        """global{} block stores ints, strings, bools, and floats in the bridge."""
        ctx = _run_source(self, """
        global {
            x       = 42
            message = "Hello Polyglot"
            flag    = True
            ratio   = 3.14
        }
        """)
        self.assertEqual(ctx.get("x"),       42)
        self.assertEqual(ctx.get("message"), "Hello Polyglot")
        self.assertEqual(ctx.get("flag"),    True)
        self.assertAlmostEqual(ctx.get("ratio"), 3.14, places=5)

    def test_02_python_sees_globals(self):
        """Python block can read bridge globals via get_global() and direct variable."""
        ctx = _run_source(self, """
        global {
            x     = 100
            label = "bridge"
        }
        python {
            assert x == 100
            assert get_global("label") == "bridge"
            export("py_saw_x",     x)
            export("py_saw_label", get_global("label"))
        }
        """)
        self.assertEqual(ctx.get("py_saw_x"),     100)
        self.assertEqual(ctx.get("py_saw_label"), "bridge")

    def test_03_python_export_returns_to_context(self):
        """Values published with export() appear in the shared bridge."""
        ctx = _run_source(self, """
        python {
            export("py_int",    500)
            export("py_str",    "from python")
            export("py_bool",   True)
            export("py_float",  2.718)
        }
        """)
        self.assertEqual(ctx.get("py_int"),  500)
        self.assertEqual(ctx.get("py_str"),  "from python")
        self.assertEqual(ctx.get("py_bool"), True)
        self.assertAlmostEqual(ctx.get("py_float"), 2.718, places=5)

    def test_04_python_to_python_function_call(self):
        """Milestone A: Python exports a function; another Python block calls it."""
        ctx = _run_source(self, """
        python {
            def add(a, b):
                return a + b
            export_function("add", add)
        }
        python {
            result = call("add", 3, 4)
            export("sum_result", result)
        }
        """)
        self.assertEqual(ctx.get("sum_result"), 7)

    # ══ Milestone B — JavaScript ═══════════════════════════════════════════

    def test_05_javascript_sees_python_export(self):
        """Milestone B: JS block reads Python export and publishes its own result."""
        ctx = _run_source(self, """
        python {
            export("py_val", "python_data")
            export("py_num", 77)
        }
        javascript {
            const data = get_global("py_val");
            const num  = get_global("py_num");
            poly_export("js_saw_py_val", data === "python_data");
            poly_export("js_doubled",   num * 2);
        }
        """)
        self.assertEqual(ctx.get("py_val"),       "python_data")
        self.assertEqual(ctx.get("py_num"),       77)
        self.assertEqual(ctx.get("js_saw_py_val"), True)
        self.assertEqual(ctx.get("js_doubled"),   154)

    # ══ Milestone C — C and C++ ════════════════════════════════════════════

    def test_06_c_export_returns_to_context(self):
        """Milestone C: C code reads bridge globals and exports values back."""
        ctx = _run_source(self, """
        global {
            base = 20
        }
        c {
            int main() {
                export_value("c_result", base + 5);
                export_value("c_flag",   (_Bool)1);
                return 0;
            }
        }
        """)
        self.assertEqual(ctx.get("c_result"), 25)
        self.assertEqual(ctx.get("c_flag"),   True)

    def test_07_cpp_export_returns_to_context(self):
        """Milestone C: C++ code reads bridge globals and exports values back."""
        ctx = _run_source(self, """
        global {
            base = 10
        }
        cpp {
            int main() {
                export_value("cpp_result", base * 3LL);
                export_value("cpp_msg",    std::string("hello from cpp"));
                return 0;
            }
        }
        """)
        self.assertEqual(ctx.get("cpp_result"), 30)
        self.assertEqual(ctx.get("cpp_msg"),    "hello from cpp")

    # ══ Milestone D — Java ═════════════════════════════════════════════════

    def test_08_java_export_returns_to_context(self):
        """Milestone D: Java reads bridge globals and exports values back."""
        ctx = _run_source(self, """
        global {
            base_val = 50
            label    = "polyglot"
        }
        java {
            class Main {
                public static void main(String[] args) {
                    export_value("java_result", base_val + 7L);
                    export_value("java_label",  label + "-java");
                }
            }
        }
        """)
        self.assertEqual(ctx.get("java_result"), 57)
        self.assertEqual(ctx.get("java_label"),  "polyglot-java")

    # ══ Milestone E — Full mixed sequential program ════════════════════════

    def test_09_mixed_full_program(self):
        """
        Milestone E: global → Python → JS → C → C++ → Java
        Each block reads from previous exports and adds its own.

        Data flow:
          base=10
          → py_val  = base * 2       = 20
          → js_val  = py_val + 5     = 25
          → c_val   = js_val + 3     = 28
          → cpp_val = c_val * 2      = 56
          → java_val = cpp_val + 1   = 57
        """
        ctx = _run_source(self, """
        global {
            base = 10
        }
        python {
            py_val = base * 2
            export("py_val", py_val)
        }
        javascript {
            const pv = get_global("py_val");
            poly_export("js_val", pv + 5);
        }
        c {
            int main() {
                export_value("c_val", js_val + 3);
                return 0;
            }
        }
        cpp {
            int main() {
                export_value("cpp_val", c_val * 2LL);
                return 0;
            }
        }
        java {
            class Main {
                public static void main(String[] args) {
                    export_value("java_val", cpp_val + 1L);
                    export_value("all_done", true);
                }
            }
        }
        """)
        self.assertEqual(ctx.get("base"),     10)
        self.assertEqual(ctx.get("py_val"),   20)
        self.assertEqual(ctx.get("js_val"),   25)
        self.assertEqual(ctx.get("c_val"),    28)
        self.assertEqual(ctx.get("cpp_val"),  56)
        self.assertEqual(ctx.get("java_val"), 57)
        self.assertEqual(ctx.get("all_done"), True)

    def test_10_object_handle_store(self):
        """bridge ObjectStore stores objects by handle and retrieves them correctly."""
        ctx = _run_source(self, "global { }")   # empty source, just need a context
        data    = {"key": "value", "num": 42}
        handle  = ctx.store_object(data)
        self.assertIsInstance(handle, int)
        self.assertGreater(handle, 0)
        retrieved = ctx.load_object(handle)
        self.assertIs(retrieved, data)
        ctx.delete_object(handle)
        self.assertIsNone(ctx.load_object(handle))


if __name__ == "__main__":
    unittest.main(verbosity=2)
