# 🚀 Phase-2 PLF — Reading Order & Quick Reference
> Open this file FIRST. It tells you exactly which file to open next.

---

## STEP 1 — Start Here: `poly.py`
**What it is:** Entry point. Reads the `.poly` file, calls `parse()` then `interpret()`.
**Key lines:** Line 15 `parse(source_code)` → Line 16 `interpret(program)`

---

## STEP 2 — Then Read: `core/ast.py`
**What it is:** 3 simple data classes. No logic. Just structure.
- `BlockNode` → holds one language block (e.g. `python { ... }`)
- `ParallelNode` → holds multiple blocks that run at the same time
- `ProgramNode` → holds the complete list of blocks

---

## STEP 3 — Then Read: `core/parser.py`
**What it is:** Reads the `.poly` source text and builds a `ProgramNode`.
**Key logic:** Finds lines ending with `{`, counts braces to find `}`, creates BlockNodes.

---

## STEP 4 — Then Read: `core/interpreter.py`
**What it is:** Walks the ProgramNode and runs each block.
**Key functions:**
- `interpret()` — main loop
- `execute_single_block()` — runs one block
- `execute_parallel()` — runs blocks in threads
- `process_global()` — handles `global { key = value }` blocks

---

## STEP 5 — Then Read: `bridge/function_registry.py`
**What it is:** The storage layer. Stores variables (`values` dict) and functions (`functions` dict).
**Key classes:** `FunctionEntry` (describes one function), `FunctionRegistry` (holds all of them)

---

## STEP 6 — Then Read: `bridge/bridge.py`
**What it is:** The main Bridge class. Wraps registry + object store + dispatcher.
**Think of it as:** The boss that delegates to registry, store, and dispatcher.

---

## STEP 7 — Then Read: `core/context.py`
**What it is:** A user-friendly wrapper around Bridge. Language runners use Context, not Bridge directly.

---

## STEP 8 — Then Read: `bridge/dispatcher.py`
**What it is:** Routes `call("fn_name", args)` to either a Python callable or a stub subprocess.

---

## STEP 9 — Then Read: `bridge/protocol.py`
**What it is:** The IPC (inter-process communication) layer. Defines the magic marker strings and manages the subprocess loop.
**Key markers to memorize:**
```
__POLY_CALL__|fn|[args]     ← subprocess asks Python to call a function
__POLY_RET__|type|value     ← Python sends return value to subprocess  
__POLY_EXPORT__|k|type|v    ← subprocess exports a value
__POLY_REGISTER__|n|l|t|src ← subprocess registers a new function
__POLY_METHOD__|h|m|[args]  ← subprocess calls a method on stored object
```

---

## STEP 10 — Then Read: `bridge/stub_runner.py`
**What it is:** Builds a tiny wrapper program in C/C++/Java/JS, runs it, and extracts the return value.

---

## STEP 11 — Then Read: `languages/adapters.py`
**What it is:** Config and helpers per language. Knows how to inject globals, compile, run, and parse exports for C, C++, JS, and Java.

---

## STEP 12 — Then Read: `languages/runner.py`
**What it is:** Uses `adapters.py` config to actually compile & run a language block. Creates temp directories, writes source files, runs gcc/javac/node, then calls `protocol.run_subprocess()`.

---

## STEP 13 — Then Read: `languages/python_lang.py`
**What it is:** Python block runner (no subprocess). Uses `exec()` to run code in-process with bridge functions injected into the environment.

---

## STEP 14 — Then Read: `languages/__init__.py`
**What it is:** The `LANGUAGE_REGISTRY` dict that maps `"python"`, `"c"`, `"java"`, etc. to their runner functions.

---

## STEP 15 — Then Read Examples
Order: `01_globals.poly` → `02_python_export.poly` → `13_full_pipeline.poly` → `20_real_life_usecase.poly`

---

## 🧠 EXAM CHEAT SHEET

### What happens when you run `poly myfile.poly`?
```
poly.py → parse() → ProgramNode
       → interpret()
             → for each block:
                   global → process_global() → context.set()
                   python → python_lang.run() → exec()
                   c/cpp  → runner.run() → gcc/g++ → subprocess → protocol
                   java   → runner.run() → javac → java → subprocess → protocol
                   js     → runner.run() → node -e → subprocess → protocol
                   parallel → ThreadPoolExecutor → concurrent blocks
```

### How do globals reach C code?
```
context.all() → inject_c_globals() → "static const long long x = 5;"
             → prepended to C source before gcc
```

### How does C export a value back?
```
C:    printf("__POLY_EXPORT__|x|int|5\n");
protocol.py: parse_export_standard(line) → {"x": 5}
interpreter: context.set("x", 5)
```

### How does JS/C call a Python function?
```
JS/C: poly_call("add", [3, 4]) → stdout: "__POLY_CALL__|add|[3,4]"
protocol.py reads this → context.call("add", 3, 4) → 7
             → encode_return(7) → "__POLY_RET__|int|7"
             → writes to subprocess stdin
JS/C receives return value from stdin
```

### What is a stub?
A **stub** is when a non-Python language registers a function that Python/other blocks can call later.
- The stub stores the source code (not a Python callable)
- When called, `stub_runner.invoke()` builds a tiny wrapper program, runs it as subprocess, and returns the result

### Key Python functions available inside a python {} block

| Function | What it does |
|----------|-------------|
| `export("name", val)` | Share val with all future language blocks |
| `export_function("name", fn)` | Register a Python fn callable from other languages |
| `get_global("name")` | Read any value from bridge |
| `call("name", *args)` | Call any function (Python or stub) |
| `store_object(obj)` | Store Python object, returns int handle |
| `load_object(handle)` | Get stored object back |

### Files organized by layer

| Layer | Files |
|-------|-------|
| **Entry** | `poly.py` |
| **Frontend (parsing)** | `core/lexer.py`, `core/ast.py`, `core/parser.py` |
| **Execution** | `core/interpreter.py`, `core/context.py` |
| **Bridge core** | `bridge/bridge.py`, `bridge/function_registry.py`, `bridge/dispatcher.py` |
| **IPC / Protocol** | `bridge/protocol.py`, `bridge/stub_runner.py` |
| **Type system** | `bridge/value_types.py`, `bridge/object_store.py` |
| **Language runners** | `languages/runner.py`, `languages/python_lang.py`, `languages/adapters.py` |
| **Templates** | `languages/templates/c_bridge.h`, `cpp_bridge.hpp`, `js_bridge.js`, `java_bridge.java` |
| **Examples** | `example/*.poly` |
