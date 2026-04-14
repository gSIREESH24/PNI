# Phase-2 Polyglot Language Framework — Walkthrough

## What Was Built

Phase-2 implements a **single shared bridge** that lets Python, JavaScript, C, C++, and Java exchange values through one common format and one shared registry.

---

## Architecture

```
                  ┌──────────────────────────────────┐
                  │           PolyBridge              │
                  │  ┌──────────┐  ┌──────────────┐  │
                  │  │ Registry │  │ ObjectStore  │  │
                  │  │ values{} │  │ handle->obj{}│  │
                  │  │ funcs{}  │  └──────────────┘  │
                  │  └──────────┘  ┌──────────────┐  │
                  │                │  Dispatcher  │  │
                  │                │ routes call()│  │
                  │                └──────────────┘  │
                  └────────────────┬─────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
        Python (exec)       JS (node -e)        C/C++/Java
         in-process          subprocess          subprocess
```

---

## Bridge Files

| File | Role |
|---|---|
| `bridge/poly_value.py` | Universal value type — INT, FLOAT, BOOL, STRING, ARRAY, OBJECT, FUNCTION, NULL |
| `bridge/registry.py` | Shared globals + function table with owner language metadata |
| `bridge/object_store.py` | Handle-based object storage for non-primitives |
| `bridge/dispatcher.py` | Routes `call(name, args)` to registered Python functions |
| `bridge/poly_bridge.py` | Central bridge API — the single interface everything uses |

---

## How the Interpreter Works

The interpreter acts as the **coordinator**, not a direct executor:

1. `global { }` block → parse `key = value` lines → store in bridge
2. `lang { }` block → send code to language adapter → receive exports dict
3. **Sync exports** → write every key/value back into bridge so the **next block sees them**

This sync-after-every-block pattern is what makes the runtime polyglot.

---

## Symbol Naming Rules

These are enforced identically across every language adapter:

| Language | Export API | Read API |
|---|---|---|
| Python | `export(name, val)` / `export_function(name, fn)` | `get_global(name)` / `call(name, *args)` |
| JavaScript | `poly_export(name, val)` | `get_global(name)` |
| C | `export_value(name, val)` macro | globals injected as `static const` vars |
| C++ | `export_value(name, val)` overloaded fn | globals injected as `static const` vars |
| Java | `export_value(name, val)` overloaded method | `get_global(name)` |

> **Note:** JavaScript uses `poly_export` instead of `export` because `export(...)` conflicts with Node.js ES module syntax.

---

## Language Adapter Summary

### Python (`languages/python_lang.py`)
- Runs **in-process** via `exec()`
- Bridge globals seeded directly into the execution environment
- `export_function()` registers a Python callable in the global function table
- `call()` dispatches through the bridge dispatcher (Milestone A: Python-to-Python call)

### JavaScript (`languages/js_lang.py`)
- Runs as a **Node.js subprocess** via `node -e`
- Bridge globals injected as `globalThis[key] = value;` lines
- Prelude defines `poly_export()` and `get_global()` on `globalThis`
- All exports collected into `__poly_exports` and serialised as JSON on the last stdout line

### C (`languages/c_lang.py`)
- Runs as a **gcc subprocess**
- Bridge globals injected as `static const <type> name = value;` declarations
- `export_value()` is a `_Generic` macro that picks the right typed printer
- Export lines use format: `__POLY_EXPORT__name|type|raw_value`

### C++ (`languages/cpp_lang.py`)
- Runs as a **g++ subprocess**
- Bridge globals injected as `static const <type> name = value;` declarations
- `export_value()` is a set of overloaded functions in `namespace polybridge`
- `using namespace polybridge;` brings them into user scope

### Java (`languages/java_lang.py`)
- Runs as a **javac + java subprocess**
- Bridge globals injected as `static final` fields in the `Main` class
- A `static {}` initialiser block populates `__globals` map for `get_global()` lookups
- `export_value()` and `get_global()` injected as `static` methods
- Two wrapping modes: bare code body wrapped in `Main.main()`, or user's own `class Main` receives injection

---

## Test Results — 10 / 10 PASSED

```
test_01_global_variable_parsing          ... ok   (Milestone A)
test_02_python_sees_globals              ... ok   (Milestone A)
test_03_python_export_returns_to_context ... ok   (Milestone A)
test_04_python_to_python_function_call   ... ok   (Milestone A — bridge call())
test_05_javascript_sees_python_export    ... ok   (Milestone B)
test_06_c_export_returns_to_context      ... ok   (Milestone C)
test_07_cpp_export_returns_to_context    ... ok   (Milestone C)
test_08_java_export_returns_to_context   ... ok   (Milestone D)
test_09_mixed_full_program               ... ok   (Milestone E)
test_10_object_handle_store              ... ok   (handle-based storage)

Ran 10 tests in 4.714s — OK
```

Run tests yourself:
```bash
python -m unittest test_phase2.py -v
```

---

## Demo Program Output (`demo_phase2.poly`)

Run the demo:
```bash
python poly.py demo_phase2.poly
```

Full output:

```
=== Phase-2 Polyglot Runtime ===

--- [GLOBAL] ---
[Bridge] globals loaded: ['x', 'message']

--- [PYTHON] ---
[Python] x       = 10
[Python] message = Hello from Global!
[Python] exported py_result = 15
[Bridge] python exported: py_result = 15

--- [JAVASCRIPT] ---
[JS] x         = 10
[JS] message   = Hello from Global!
[JS] py_result = 15
[JS] exported js_result = 30
[Bridge] javascript exported: js_result = 30

--- [C] ---
[C] x         = 10
[C] message   = Hello from Global!
[C] js_result = 30
[C] exported c_result = 40
[Bridge] c exported: c_result = 40

--- [CPP] ---
[C++] x         = 10
[C++] message   = Hello from Global!
[C++] c_result  = 40
[C++] exported cpp_result = 80
[Bridge] cpp exported: cpp_result = 80

--- [JAVA] ---
[Java] x          = 10
[Java] message    = Hello from Global!
[Java] cpp_result = 80
[Java] exported java_result = 180
[Bridge] java exported: java_result = 180
[Bridge] java exported: final_status = 'Phase-2 Complete!'

=== Final Bridge State ===
  c_result      = 40
  cpp_result    = 80
  final_status  = 'Phase-2 Complete!'
  java_result   = 180
  js_result     = 30
  message       = 'Hello from Global!'
  py_result     = 15
  x             = 10
```

### Data Flow at a Glance

```
global { x=10, message="Hello from Global!" }
    |
    +--> Python  : py_result  = x + 5           = 15
    |
    +--> JS      : js_result  = py_result * 2   = 30
    |
    +--> C       : c_result   = js_result + 10  = 40
    |
    +--> C++     : cpp_result = c_result * 2    = 80
    |
    +--> Java    : java_result = cpp_result + 100 = 180
                               final_status = "Phase-2 Complete!"
```

---

## What Phase-2 Does NOT Include (by design)

The following are explicitly out of scope for Phase-2 and belong to later phases:

- Full JNI internals / native memory access
- GC sharing across language runtimes
- Reflection across languages
- Inheritance across languages
- Reverse subprocess calls (JS / C / C++ / Java calling back into Python at runtime)
- Threads / concurrent execution
- Shared heap objects

---

## File Structure

```
Phase_2_PLF/
├── bridge/
│   ├── __init__.py          ← exports all bridge classes
│   ├── poly_value.py        ← universal value format
│   ├── registry.py          ← shared globals + function table
│   ├── object_store.py      ← handle-based object storage
│   ├── dispatcher.py        ← routes call() to registered functions
│   └── poly_bridge.py       ← central bridge API
├── core/
│   ├── ast.py               ← BlockNode, ProgramNode (unchanged)
│   ├── parser.py            ← .poly file parser (unchanged)
│   ├── context.py           ← runtime wrapper around PolyBridge
│   └── interpreter.py       ← coordinator (process global, route, sync)
├── languages/
│   ├── __init__.py          ← LANGUAGE_REGISTRY mapping
│   ├── python_lang.py       ← Python adapter
│   ├── js_lang.py           ← JavaScript adapter
│   ├── c_lang.py            ← C adapter
│   ├── cpp_lang.py          ← C++ adapter
│   └── java_lang.py         ← Java adapter
├── test_phase2.py           ← 10 tests covering Milestones A-E
├── demo_phase2.poly         ← final verification program
└── poly.py                  ← CLI entry point
```
