# 📖 Phase-2 Polyglot Runtime Framework — Complete Study Guide

---

## 🗂️ HOW TO READ THIS PROJECT (Reading Order)

Read the files in this exact order — each one builds on the previous:

```
READING ORDER:
1.  poly.py                          ← Entry Point (START HERE)
2.  core/lexer.py                    ← Tokenizer (splits source code into lines)
3.  core/ast.py                      ← AST Node definitions (data structures)
4.  core/parser.py                   ← Parser (converts lines → AST tree)
5.  core/context.py                  ← Shared memory (the bridge between all languages)
6.  core/interpreter.py              ← Executor (walks the AST and runs code)
7.  bridge/value_types.py            ← Type system (how values are represented)
8.  bridge/function_registry.py      ← Function & value storage
9.  bridge/object_store.py           ← Object handle system
10. bridge/bridge.py                 ← Main Bridge class (glues everything together)
11. bridge/dispatcher.py             ← Routes function calls to the right runner
12. bridge/protocol.py               ← Wire protocol (how Python talks to subprocesses)
13. bridge/stub_runner.py            ← Calls cross-language stubs
14. bridge/__init__.py               ← Exports the bridge package
15. languages/adapters.py            ← Per-language code transformations
16. languages/runner.py              ← Compiles & runs C/C++/Java/JS subprocesses
17. languages/python_lang.py         ← Python block runner (in-process)
18. languages/__init__.py            ← Language registry (maps names → runners)
19. languages/templates/             ← Bridge glue code for each language
20. example/01_globals.poly → ...    ← Example .poly files (read after above)
```

---

## 🧠 BIG PICTURE — What Does This Project Do?

This is a **Polyglot Runtime Framework (PLF)**. It lets you write a **single `.poly` file** that contains code blocks in **multiple languages** (Python, JavaScript, C, C++, Java), and they all **share data** through a central bridge.

```
┌─────────────────────────────────────────────────────────┐
│                   my_program.poly                        │
│                                                           │
│  global { ... }    ← shared variables                    │
│  python { ... }    ← Python code                         │
│  javascript { ... }← JS code                             │
│  c { ... }         ← C code                              │
│  cpp { ... }       ← C++ code                            │
│  java { ... }      ← Java code                           │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
                      poly.py runs it
                             │
              ┌──────────────▼──────────────┐
              │         BRIDGE              │
              │  (shared memory for all     │
              │   languages to read/write)  │
              └─────────────────────────────┘
```

**Key idea:** Every language can read globals from the bridge and export its results back to the bridge so the next language block can use them.

---

## FILE 1 — `poly.py` (Entry Point)

> **Role:** The very first thing that runs when you type `poly myfile.poly`.

### Full Code Explained Line by Line

```python
import sys
from core.parser import parse
from core.interpreter import interpret

def main():
    if len(sys.argv) != 2:         # Must pass exactly 1 filename argument
        print("Usage: poly file.poly")
        return

    file_path = sys.argv[1]        # Get the .poly file from command line

    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()     # Read the entire .poly file as a string

    program = parse(source_code)   # Step 1: Parse → builds an AST (tree of blocks)
    interpret(program)             # Step 2: Interpret → execute each block

if __name__ == "__main__":
    main()
```

### Flowchart

```
User types: poly example/01_globals.poly
         │
         ▼
    poly.py → main()
         │
         ├─ Read file content (string)
         │
         ├─ parse(source_code) ──→ ProgramNode (tree of blocks)
         │
         └─ interpret(program) ──→ Execute each block in order
```

---

## FILE 2 — `core/lexer.py` (Tokenizer)

> **Role:** Splits the source code into individual lines.

### Full Code

```python
def tokenize(source_code):
    return source_code.splitlines()
```

### Explanation

This is the simplest file in the project. It takes the entire `.poly` file as one big string and splits it into a **list of lines**.

**Example:**
```
Input:  "global {\n    x = 5\n}"
Output: ["global {", "    x = 5", "}"]
```

> ⚠️ **Note:** The `tokenize` function exists but is actually **not called** by the parser (the parser does its own `splitlines()`). This file is a leftover/placeholder for potential future use.

---

## FILE 3 — `core/ast.py` (Abstract Syntax Tree Nodes)

> **Role:** Defines the **data structures** (classes) that represent a parsed `.poly` program.

### Full Code Explained

```python
class BlockNode:
    def __init__(self, language, code):
        self.language = language   # e.g. "python", "javascript", "c"
        self.code = code           # the raw code inside the { } block

class ParallelNode:
    def __init__(self, blocks):
        self.blocks = blocks       # a list of BlockNodes to run at the same time

class ProgramNode:
    def __init__(self, blocks):
        self.blocks = blocks       # ordered list of BlockNodes / ParallelNodes
```

### What Is an AST?

An **Abstract Syntax Tree (AST)** is a tree-shaped data structure that represents the structure of your program, NOT the raw text.

**Example `.poly` file:**
```
python { print("Hi") }
javascript { console.log("Hello") }
```

**Becomes this AST:**
```
ProgramNode
├── BlockNode(language="python",     code='print("Hi")')
└── BlockNode(language="javascript", code='console.log("Hello")')
```

### Flowchart of Node Types

```
ProgramNode
    │
    ├── BlockNode       ← normal single-language block
    │     ├── .language = "python" / "c" / "java" / etc.
    │     └── .code     = raw source code string
    │
    └── ParallelNode    ← parallel { ... } wrapper
          └── .blocks   = [BlockNode, BlockNode, ...]
                          (these run simultaneously)
```

---

## FILE 4 — `core/parser.py` (Parser)

> **Role:** Reads the list of lines and builds the **ProgramNode AST tree**.

### Full Code Explained

```python
import textwrap
from core.ast import BlockNode, ProgramNode, ParallelNode

def parse(source_code):
    lines = source_code.splitlines()   # Split into lines
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # RULE 1: Skip empty lines, // comments, and # comments
        if not stripped or stripped.startswith("//") or stripped.startswith("#"):
            i += 1
            continue

        # RULE 2: A line ending with { starts a new block
        if stripped.endswith("{"):
            lang = stripped[:-1].strip().lower()   # Extract language name
            block_lines = []
            brace_depth = 1                        # Track nested braces
            i += 1

            # Read lines until we find the matching closing }
            while i < len(lines) and brace_depth > 0:
                inner_line = lines[i]
                brace_depth += inner_line.count("{")
                brace_depth -= inner_line.count("}")
                if brace_depth > 0:
                    block_lines.append(inner_line)
                i += 1

            content = textwrap.dedent("\n".join(block_lines))  # Remove leading spaces

            # SPECIAL CASE: parallel block → recurse and create ParallelNode
            if lang == "parallel":
                inner_program = parse(content)
                blocks.append(ParallelNode(inner_program.blocks))
            else:
                blocks.append(BlockNode(lang, content))
        else:
            i += 1

    return ProgramNode(blocks)
```

### Key Concepts

**Brace Depth Counting:**
The parser uses `brace_depth` to handle nested `{}` inside C/Java/JS code:
```
python {            ← brace_depth = 1 (enter block)
    if True: {      ← brace_depth = 2
    }               ← brace_depth = 1
}                   ← brace_depth = 0 → block ends
```

### Flowchart — How Parser Processes a `.poly` File

```
source_code (string)
       │
       ▼
  splitlines() → ["global {", "    x=5", "}", "python {", ...]
       │
       ▼
  Loop through lines:
       │
       ├─ Empty / comment? → SKIP
       │
       ├─ Ends with "{"? → BLOCK START
       │       │
       │       ├─ Extract language name (e.g. "python")
       │       │
       │       ├─ Read lines until matching "}" (brace depth = 0)
       │       │
       │       ├─ lang == "parallel"? → ParallelNode (recursive parse)
       │       │
       │       └─ else → BlockNode(lang, code)
       │
       └─ Other line? → SKIP
       
       ▼
  ProgramNode([block1, block2, ...])
```

---

## FILE 5 — `core/context.py` (Shared Context / Bridge Wrapper)

> **Role:** The **shared memory** that all language blocks read from and write to. It's a friendly Python interface over the Bridge.

### Full Code Explained

```python
from bridge import Bridge

class Context:

    def __init__(self, bridge: Bridge = None):
        # Create a Bridge if not given. Bridge holds all data.
        self.bridge = bridge if bridge is not None else Bridge()

    # ── Variable storage ──────────────────────────────────────
    def set(self, key, value):
        self.bridge.set(key, value)      # Store a key-value pair

    def get(self, key, default=None):
        return self.bridge.get(key, default)  # Retrieve a value

    def all(self) -> dict:
        return self.bridge.all_values()  # Get all stored values as a dict

    # ── Function registration ─────────────────────────────────
    def register_python_function(self, name, func, param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    def export_function(self, name, func, language="python", param_types=None, return_type=None):
        self.bridge.register_python_function(name, func, param_types, return_type)

    # ── Class schema registration ─────────────────────────────
    def register_class_schema(self, name, fields):
        self.bridge.register_class_schema(name, fields)

    def export_class_schema(self, name, fields):
        self.bridge.register_class_schema(name, fields)

    # ── Function lookup ───────────────────────────────────────
    def has_function(self, name) -> bool:
        return self.bridge.has_function(name)

    def get_function(self, name):
        entry = self.bridge.registry.get_function(name)
        return entry.func if entry is not None else None

    # ── Stub registration (C/C++/Java/JS functions) ───────────
    def register_function_stub(self, name, language, source, return_type="int"):
        self.bridge.register_stub(name, language, source, return_type)

    # ── Function calling ───────────────────────────────────────
    def call(self, name, *args):
        return self.bridge.call(name, *args, context=self)

    # ── Object store (for complex Python objects) ─────────────
    def store_object(self, obj) -> int:
        return self.bridge.store_object(obj)   # Returns a numeric handle

    def load_object(self, handle):
        return self.bridge.load_object(handle) # Retrieve by handle

    def delete_object(self, handle):
        self.bridge.delete_object(handle)

    def call_method(self, handle, method, *args):
        return self.bridge.call_method(handle, method, *args)
```

### What Is "Context"?

Think of Context as a **shared whiteboard** in a classroom:
- Any language block can **write** on it (`context.set(...)`)
- Any language block can **read** from it (`context.get(...)`)
- Functions can be registered and called cross-language

### Flowchart — Context as a Hub

```
                  ┌──────────────────────┐
                  │      Context         │
                  │  (shared whiteboard) │
                  └──────┬───────────────┘
                         │
         ┌───────────────┼───────────────────┐
         │               │                   │
   Python block    C block writes      JS block reads
   writes x=5      score=870           uses x and score
```

---

## FILE 6 — `core/interpreter.py` (Interpreter / Executor)

> **Role:** Walks the ProgramNode tree and **executes** each block in order.

### Full Code Explained — Function by Function

#### `interpret(program_node)` — Main Entry
```python
def interpret(program_node):
    context = Context()                  # Create the shared bridge/context
    print("\n=== Phase-2 Polyglot Runtime ===\n")

    for block in program_node.blocks:   # Loop through every block in order
        if isinstance(block, ParallelNode):
            execute_parallel(block.blocks, context)   # Run parallel blocks
            continue
        lang = block.language
        code = block.code
        execute_single_block(lang, code, context)     # Run normal block

    # Print final summary of all bridge values
    print("\n=== Final Bridge State ===")
    for k, v in sorted(context.all().items()):
        if not callable(v):
            print(f"  {k} = {v!r}")
    fns = context.bridge.list_functions()
    if fns:
        print(f"  registered functions: {fns}")
```

#### `execute_single_block(lang, code, context)` — Runs One Block
```python
def execute_single_block(lang, code, context):
    print(f"--- [{lang.upper()}] ---", flush=True)

    if lang == "global":                             # SPECIAL: global block
        process_global(code, context)               # Parse key=value lines
        print(f"[Bridge] globals loaded: {list(context.all().keys())}")
        return

    runner = LANGUAGE_REGISTRY.get(lang)            # Find the right runner
    if runner is None:
        print(f"[Bridge] ERROR — unsupported language: '{lang}'")
        return

    try:
        result = runner(code, context)              # RUN THE CODE
        exports = result[0] if isinstance(result, tuple) else result
    except Exception as exc:
        print(f"[Bridge] ERROR in {lang} block: {exc}")
        exports = {}

    if isinstance(exports, dict):                   # Save exports to bridge
        for key, value in exports.items():
            context.set(key, value)
            if callable(value):
                print(f"[Bridge] {lang} registered function: {key!r}")
            else:
                print(f"[Bridge] {lang} exported: {key} = {value!r}")
```

#### `execute_parallel(blocks, context)` — Parallel Execution
```python
def execute_parallel(blocks, context):
    print(f"=== [PARALLEL PHASE START] ===", flush=True)

    def run_worker(block):
        output_buffer = io.StringIO()           # Capture print output
        with redirect_stdout(output_buffer):
            execute_single_block(block.language, block.code, context)
        return block.language, output_buffer.getvalue()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_worker, b) for b in blocks]
        for future in concurrent.futures.as_completed(futures):
            lang, output = future.result()
            print(output, end="")     # Print each block's output after it finishes

    print(f"=== [PARALLEL PHASE END] ===", flush=True)
```

#### `process_global(code, context)` — Processes `global {}` blocks
```python
def process_global(code, context):
    for line in code.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, _, raw_value = line.partition("=")  # Split on first "="
        key = key.strip()
        raw_value = raw_value.strip()

        try:
            # Try to evaluate the value as a Python literal
            parsed_value = py_ast.literal_eval(raw_value)   # "True" → True, "3.14" → 3.14
        except Exception:
            parsed_value = raw_value    # If can't evaluate, keep as string

        context.set(key, parsed_value)
```

### Flowchart — Interpreter Execution Flow

```
interpret(ProgramNode)
       │
       ├── Create Context (empty bridge)
       │
       ├── For each block:
       │       │
       │       ├── ParallelNode?
       │       │       └── execute_parallel() → ThreadPoolExecutor
       │       │               ├── run_worker(block1) ─┐  (concurrent)
       │       │               ├── run_worker(block2) ─┤
       │       │               └── run_worker(block3) ─┘
       │       │
       │       └── BlockNode?
       │               │
       │               ├── lang == "global"? → process_global()
       │               │       └── Parse "key = value" lines → context.set()
       │               │
       │               └── else → LANGUAGE_REGISTRY[lang](code, context)
       │                       └── returns {"key": value, ...} exports
       │                               └── context.set(key, value) for each
       │
       └── Print Final Bridge State
```

---

## FILE 7 — `bridge/value_types.py` (Type System)

> **Role:** Defines the universal type system that works across ALL languages.

### Full Code Explained

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any

class PolyType(Enum):
    NULL     = "null"       # No value
    INT      = "int"        # Integer number
    FLOAT    = "float"      # Decimal number
    BOOL     = "bool"       # True / False
    STRING   = "string"     # Text
    ARRAY    = "array"      # List of values
    OBJECT   = "object"     # Complex Python object
    FUNCTION = "function"   # Callable
    ERROR    = "error"      # Error state

@dataclass
class PolyValue:
    type:  PolyType
    value: Any = None

    @staticmethod
    def null():
        return PolyValue(PolyType.NULL, None)

    @staticmethod
    def from_python(value):
        # Convert any Python value → PolyValue
        if value is None:           return PolyValue.null()
        if isinstance(value, bool): return PolyValue(PolyType.BOOL,     value)
        if isinstance(value, int):  return PolyValue(PolyType.INT,      value)
        if isinstance(value, float):return PolyValue(PolyType.FLOAT,    value)
        if isinstance(value, str):  return PolyValue(PolyType.STRING,   value)
        if isinstance(value, list): return PolyValue(PolyType.ARRAY,    ...)
        if callable(value):         return PolyValue(PolyType.FUNCTION,  value)
        return PolyValue(PolyType.OBJECT, value)

    def to_python(self):
        # Convert PolyValue → Python value
        if self.type == PolyType.NULL:  return None
        if self.type == PolyType.ARRAY: return [v.to_python() ... for v in self.value]
        return self.value
```

### Why Is This Needed?

Different languages have different type systems. `PolyValue` is a **universal wrapper** so the bridge knows what type a value is regardless of where it came from.

```
Python int 42    →  PolyValue(INT, 42)
JS number 42     →  PolyValue(INT, 42)
C long long 42   →  PolyValue(INT, 42)
Java long 42     →  PolyValue(INT, 42)
```

---

## FILE 8 — `bridge/function_registry.py` (Registry)

> **Role:** Stores all variables (values) and function registrations for the bridge.

### Full Code Explained

```python
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class FunctionEntry:
    name:        str                  # Function name e.g. "add"
    language:    str                  # "python", "c", "java", etc.
    func:        Any  = None          # Actual callable (for Python functions)
    param_types: list = field(...)    # e.g. ["int", "float"]
    return_type: str  = None          # e.g. "float"
    stub_source: str  = None          # Source code (for C/C++/Java/JS stubs)

class FunctionRegistry:

    def __init__(self):
        self.values        = {}  # { "x": 5, "name": "hello" }   ← all bridge variables
        self.functions     = {}  # { "add": FunctionEntry(...) }  ← all registered functions
        self.class_schemas = {}  # { "Point": {"x":"int","y":"int"} } ← class definitions

    def set_value(self, name, value):
        self.values[name] = value          # Store a variable

    def get_value(self, name, default=None):
        return self.values.get(name, default)

    def register_class_schema(self, name, fields):
        self.class_schemas[name] = fields  # Register a class structure

    def register_python_function(self, name, func, param_types=None, return_type=None):
        self.functions[name] = FunctionEntry(
            name=name, language="python", func=func,
            param_types=param_types or [], return_type=return_type,
        )

    def register_stub(self, name, language, source, return_type="int"):
        self.functions[name] = FunctionEntry(
            name=name, language=language, func=None,
            return_type=return_type, stub_source=source,  # No callable — just source code
        )

    def get_function(self, name) -> Optional[FunctionEntry]:
        return self.functions.get(name)

    def has_function(self, name) -> bool:
        return name in self.functions

    def list_functions(self) -> list:
        return list(self.functions.keys())
```

### Two Types of Functions

| Type | `func` field | `stub_source` field | How it runs |
|------|-------------|---------------------|-------------|
| Python function | ✅ Callable | None | Called directly in Python |
| Stub (C/JS/Java) | None | ✅ Source code string | Compiled/run as subprocess |

---

## FILE 9 — `bridge/object_store.py` (Object Store)

> **Role:** Stores complex Python objects and gives them a numeric **handle** (ID) that other languages can reference.

### Full Code Explained

```python
class ObjectStore:

    def __init__(self):
        self._objects = {}   # { 1: <MyObject>, 2: <AnotherObject> }
        self._next_id = 1    # Counter starts at 1

    def put(self, obj) -> int:
        handle = self._next_id       # Assign next available ID
        self._objects[handle] = obj  # Store the object
        self._next_id += 1           # Increment counter
        return handle                # Return the handle (integer)

    def get(self, handle):
        return self._objects.get(handle)   # Retrieve by handle

    def delete(self, handle):
        self._objects.pop(handle, None)    # Remove from store

    def __len__(self):
        return len(self._objects)          # How many objects stored
```

### Why Handles?

Languages like C, C++, Java cannot directly hold a Python object. Instead, Python stores the object and gives back an **integer handle**. The other language passes that integer around, and when it needs to call a method, it sends the handle back to Python.

```
Python: obj = MyClass()
        handle = store_object(obj)   → returns 1
        export("my_handle", 1)

C:     // receives my_handle = 1
       // sends __POLY_METHOD__|1|method_name|[args] back to Python
```

---

## FILE 10 — `bridge/bridge.py` (The Bridge Class)

> **Role:** The **central glue** class. It owns the registry, object store, and dispatcher, and provides one clean API.

### Full Code Explained

```python
from .function_registry import FunctionRegistry
from .object_store      import ObjectStore
from .dispatcher        import Dispatcher

class Bridge:

    def __init__(self):
        self.registry   = FunctionRegistry()       # Stores values + functions
        self.store      = ObjectStore()            # Stores complex objects
        self.dispatcher = Dispatcher(self.registry) # Routes function calls

    # --- Variable management ---
    def set(self, name, value):
        self.registry.set_value(name, value)

    def get(self, name, default=None):
        return self.registry.get_value(name, default)

    def all_values(self) -> dict:
        return dict(self.registry.values)

    # --- Function management ---
    def register_python_function(self, name, func, param_types=None, return_type=None):
        self.registry.register_python_function(name, func, param_types, return_type)

    def register_class_schema(self, name, fields):
        self.registry.register_class_schema(name, fields)

    def register_stub(self, name, language, source, return_type="int"):
        self.registry.register_stub(name, language, source, return_type)

    def call(self, name, *args, context=None):
        return self.dispatcher.call(name, *args, context=context)  # Route to dispatcher

    def has_function(self, name) -> bool:
        return self.registry.has_function(name)

    def list_functions(self) -> list:
        return self.registry.list_functions()

    # --- Object store management ---
    def store_object(self, obj) -> int:
        return self.store.put(obj)

    def load_object(self, handle):
        return self.store.get(handle)

    def delete_object(self, handle):
        self.store.delete(handle)

    def call_method(self, handle, method, *args):
        obj = self.load_object(handle)
        if obj is None:
            raise ValueError(f"[Bridge] Invalid handle: {handle}")
        return getattr(obj, method)(*args)   # Call Python object's method
```

### Bridge Architecture Diagram

```
         Bridge
        ┌──────────────────────────────────┐
        │                                  │
        │   FunctionRegistry               │
        │   ├── values dict                │
        │   ├── functions dict             │
        │   └── class_schemas dict         │
        │                                  │
        │   ObjectStore                    │
        │   └── _objects dict (handle → obj)│
        │                                  │
        │   Dispatcher                     │
        │   └── routes call() to runners   │
        │                                  │
        └──────────────────────────────────┘
```

---

## FILE 11 — `bridge/dispatcher.py` (Function Router)

> **Role:** When someone calls `context.call("add", 3, 4)`, the Dispatcher decides **how** to call it — directly (Python) or via a subprocess stub (C/Java/JS).

### Full Code Explained

```python
from .function_registry import FunctionRegistry
from . import stub_runner

class Dispatcher:

    def __init__(self, registry: FunctionRegistry):
        self._registry = registry

    def call(self, name, *args, context=None):
        entry = self._registry.get_function(name)

        if entry is None:
            raise NameError(f"[Bridge] Function '{name}' is not registered.")

        # CASE 1: Python function — call directly
        if entry.func is not None:
            return entry.func(*args)

        # CASE 2: Stub (C/C++/Java/JS) — run via subprocess
        if entry.stub_source is not None:
            return stub_runner.invoke(
                fn_name     = entry.name,
                language    = entry.language,
                source      = entry.stub_source,
                return_type = entry.return_type or "int",
                args        = list(args),
                context     = context,
            )

        raise RuntimeError(f"[Bridge] Function '{name}' has no callable.")
```

### Flowchart — Dispatcher Decision

```
context.call("my_func", 10, 20)
         │
         ▼
Dispatcher.call("my_func", 10, 20)
         │
         ├── Look up "my_func" in registry
         │
         ├── entry.func is not None?
         │       YES → call entry.func(10, 20) directly (Python)
         │       NO  ↓
         │
         └── entry.stub_source is not None?
                 YES → stub_runner.invoke(...)
                       ├── Build C/Java/JS snippet
                       ├── Compile & run subprocess
                       └── Return the result
                 NO  → RuntimeError
```

---

## FILE 12 — `bridge/protocol.py` (Wire Protocol)

> **Role:** Defines how Python **talks to** C/C++/Java/JS subprocesses through **stdin/stdout** using special marker strings.

### The Markers (Magic Strings)

```python
CALL_MARKER     = "__POLY_CALL__|"      # Subprocess wants to call a Python function
RETURN_MARKER   = "__POLY_RET__|"       # Return value from Python → subprocess
REGISTER_MARKER = "__POLY_REGISTER__|"  # Subprocess registering a new function
METHOD_MARKER   = "__POLY_METHOD__|"    # Subprocess calling a method on a Python object
```

### `encode_return(value)` — Python value → text line

```python
def encode_return(value) -> str:
    # Converts a Python value to a text line to send to subprocess
    if value is None:   return "__POLY_RET__|null|null\n"
    if isinstance(value, bool): return "__POLY_RET__|bool|true\n"  # or false
    if isinstance(value, int):  return "__POLY_RET__|int|42\n"
    if isinstance(value, float):return "__POLY_RET__|float|3.14\n"
    if isinstance(value, str):  return "__POLY_RET__|str|hello\n"
```

### `decode_return(line)` — text line → Python value

```python
def decode_return(line):
    # Parses "__POLY_RET__|int|42" → returns Python int 42
    body = line[len("__POLY_RET__|"):]     # Remove the marker prefix
    sep  = body.find("|")
    typ, val = body[:sep], body[sep + 1:]  # Split into type and value
    if typ == "int":   return int(val)
    if typ == "float": return float(val)
    if typ == "bool":  return val.lower() == "true"
    if typ == "null":  return None
    return val  # string
```

### `run_subprocess(cmd, context, parse_export_line)` — The Core IPC Loop

This is the **heart** of cross-language communication. It:
1. Starts a subprocess (C/Java/JS program) via `subprocess.Popen`
2. Reads each line from its stdout
3. Routes lines based on which marker they start with
4. Responds to `CALL_MARKER` lines by calling Python functions
5. Collects `EXPORT` lines as results

```
SUBPROCESS STDOUT                          PYTHON HANDLES
─────────────────                          ──────────────
__POLY_CALL__|add|[3,4]          →  calls context.call("add", 3, 4)
                                         then sends back:
                               ←  __POLY_RET__|int|7

__POLY_EXPORT__|score|int|870    →  exports["score"] = 870

__POLY_REGISTER__|fn|c|int|src   →  register new C stub
[anything else]                  →  print it (normal output)
```

### Flowchart — run_subprocess

```
run_subprocess(["./main.exe"], context, parse_export_line)
       │
       ├── Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
       │
       ├── Thread: drain stderr (run in background)
       │
       └── Loop reading stdout lines:
               │
               ├── __POLY_CALL__?    → call Python fn, send return value back
               ├── __POLY_METHOD__?  → call method on stored object, send back
               ├── __POLY_REGISTER__?→ register stub in context
               ├── __POLY_EXPORT__?  → add to exports dict
               ├── __POLY_RET__?     → capture as stub return value
               └── else              → print line as normal output
               │
       └── wait() for process to finish
       └── return (exports_dict, stub_return_value)
```

---

## FILE 13 — `bridge/stub_runner.py` (Cross-Language Stub Invoker)

> **Role:** When you call a C/C++/Java/JS function from Python, this module builds a tiny executable program, runs it, and gets the return value.

### How It Works (Step by Step)

**Example:** Calling a C function `add(long long a, long long b)` with args `[3, 4]`:

1. `stub_runner.invoke("add", "c", source_code, "int", [3, 4], context)` is called
2. `_run_c_stub` builds this wrapper:
   ```c
   // user's source code (contains add() function)
   int add(long long a, long long b) { return a + b; }
   
   // auto-generated main
   int main(void) {
       printf("__POLY_RET__|int|%lld\n", (long long)(add(3LL, 4LL)));
       return 0;
   }
   ```
3. This is passed to `languages/runner.py` which compiles & runs it
4. The output `__POLY_RET__|int|7` is captured and decoded → returns `7`

### Language-Specific Helpers

| Function | Purpose |
|----------|---------|
| `_c_literal(v)` | Convert Python value → C literal string (`42` → `42LL`, `"hi"` → `"hi"`) |
| `_java_literal(v)` | Convert Python value → Java literal (42 → `42L`, True → `true`) |
| `_run_js_stub(...)` | Run JavaScript function using Node.js inline snippet |
| `_run_c_stub(...)` | Compile & run C function |
| `_run_cpp_stub(...)` | Compile & run C++ function |
| `_run_java_stub(...)` | Compile & run Java static method |
| `invoke(...)` | Entry point — dispatches to the right `_run_X_stub` |

---

## FILE 14 — `bridge/__init__.py` (Package Exports)

> **Role:** Makes the bridge folder a Python package and exposes its most important classes.

```python
from .bridge            import Bridge
from .function_registry import FunctionRegistry, FunctionEntry
from .object_store      import ObjectStore
from .dispatcher        import Dispatcher
from .protocol          import run_subprocess, encode_return, decode_return
from .value_types       import PolyType, PolyValue

__all__ = ["Bridge", "FunctionRegistry", ...]
```

This means anywhere in the project, you can write:
```python
from bridge import Bridge
```
Instead of the longer:
```python
from bridge.bridge import Bridge
```

---

## FILE 15 — `languages/adapters.py` (Language Adapters Config)

> **Role:** For each supported language, defines HOW to: inject globals, compile, run, and parse exports.

### Key Sections

#### Export Parsing

```python
EXPORT_PREFIX = "__POLY_EXPORT__"

def _parse_export_standard(line):
    # Parses: "__POLY_EXPORT__|score|int|870"
    # Returns: {"score": 870}
    if not line.startswith(EXPORT_PREFIX): return None
    name, type_name, raw = payload.split("|", 2)
    if type_name == "int":    return {name: int(raw)}
    if type_name == "double": return {name: float(raw)}
    if type_name == "bool":   return {name: raw.lower() == "true"}
    if type_name == "string": return {name: raw}
    if type_name == "json":   return {name: json.loads(raw)}

def _parse_export_js(line):
    # JS exports as JSON: "__POLY_EXPORT__{"score": 870}"
    data = json.loads(line[len("__POLY_EXPORT__"):])
    return data  # already a dict
```

#### Global Injection

Before running a C/C++/Java/JS block, the framework **injects** all bridge variables. For example:

**`_inject_c_globals(context)`** generates:
```c
static const long long version = 2;
static const double pi = 3.14159;
static const char* app_name = "PolyBridge";
static const bool debug_mode = 1;
```

**`_inject_java_members(context)`** generates:
```java
static final long version = 2L;
static final double pi = 3.14159;
static final String app_name = "PolyBridge";
static final boolean debug_mode = true;
static final Map<String,Object> __globals = new HashMap<>();
static { __globals.put("version", version); ... }
public static Object get_global(String name) { return __globals.get(name); }
```

#### The ADAPTERS Dictionary

```python
ADAPTERS = {
    "c": {
        "template":       "templates/c_bridge.h",      # Bridge helper code
        "suffix":         ".c",                         # File extension
        "compile":        lambda src, out: ["gcc", ...],# Compile command
        "run_cmd":        lambda out, _bd: [out],        # Run command
        "inject_globals": _inject_c_globals,            # Inject bridge vars
        "inject_classes": _inject_c_classes,            # Inject class structs
        "parse_export":   _parse_export_standard,       # How to read exports
        "wrap_source":    None,                         # No wrapping needed
        "preprocess":     None,                         # No preprocessing
    },
    "javascript": { ... "compile": None, "run_cmd": None ... },
    # JS is run inline by node -e "..." — no file needed
    "java": {
        "wrap_source": _wrap_java,   # Java needs to be wrapped in a class
        ...
    },
}
```

---

## FILE 16 — `languages/runner.py` (Subprocess Runner)

> **Role:** Given a language and source code, prepares the full source file, compiles it (if needed), and runs it.

### Full Code Explained

```python
def run(lang, code, context) -> tuple:
    cfg = ADAPTERS[lang]             # Get config for this language

    # Step 1: Preprocess (e.g. normalize JS exports)
    if cfg["preprocess"]:
        code = cfg["preprocess"](code)

    # Step 2: Inject globals from the bridge
    globals_block = cfg["inject_globals"](context) if cfg["inject_globals"] else ""

    # Step 3: Inject class schemas
    classes_block = cfg["inject_classes"](context) if cfg["inject_classes"] else ""

    # Step 4: Read bridge template (helper macros/functions)
    with open(cfg["template"]) as f:
        bridge_glue = f.read()

    # Step 5 (JavaScript only): Run inline, no temp file
    if lang == "javascript":
        full_js = globals_block + bridge_glue + code + export_dump
        return run_subprocess(["node", "-e", full_js], context, cfg["parse_export"])

    # Step 6: For C/C++/Java: create temp directory + source file
    build_dir = tempfile.mkdtemp(prefix=f"plf_{lang}_")

    try:
        # Assemble the full source
        if cfg["wrap_source"]:                    # Java needs class wrapping
            full_source = cfg["wrap_source"](code, globals_block + bridge_glue, context)
        else:                                     # C/C++: just concatenate
            full_source = globals_block + bridge_glue + classes_block + code

        # Write to temp file (Main.java or main.c or main.cpp)
        with open(src_path, "w") as f:
            f.write(full_source)

        # Step 7: Compile (if needed)
        if cfg["compile"]:
            compile_cmd = cfg["compile"](src_path, out_path)
            cp = subprocess.run(compile_cmd, ...)
            if cp.returncode != 0:
                print("Compilation error:", cp.stderr)
                return {}, None

        # Step 8: Run the binary/jar
        run_cmd = cfg["run_cmd"](out_path, build_dir)
        return run_subprocess(run_cmd, context, cfg["parse_export"])

    finally:
        shutil.rmtree(build_dir)   # Always clean up temp files
```

### Flowchart — Runner for C code

```
run("c", "int main(){...}", context)
       │
       ├── Inject globals → "static const long long x = 5;"
       ├── Read c_bridge.h → helper macros
       ├── Concatenate: globals + bridge_h + user_code
       ├── Write to /tmp/plf_c_XXX/main.c
       ├── gcc -std=c11 main.c -o main.exe
       ├── Execute ./main.exe (subprocess)
       │       │
       │       └── stdout → run_subprocess() reads markers
       │
       ├── Cleanup /tmp/plf_c_XXX/
       └── Return (exports_dict, stub_return)
```

---

## FILE 17 — `languages/python_lang.py` (Python Runner)

> **Role:** Executes a Python code block **in-process** (no subprocess), with access to all bridge functions.

### Full Code Explained

```python
def run(code: str, context) -> dict:
    exports: dict = {}

    # ── Helper functions injected into the Python block's environment ──

    def export(name, value):
        """Makes a value available to future blocks."""
        context.set(name, value)   # Store in bridge
        exports[name] = value      # Track for this block's return

    def export_function(name, func, param_types=None, return_type=None):
        """Registers a Python function that other languages can call."""
        context.export_function(name, func, ...)
        exports[name] = func

    def export_class(name, cls, fields):
        """Registers a class schema so C/Java/JS can create matching structs."""
        context.export_class_schema(name, fields)
        exports[name] = cls

    def get_global(name, default=None):
        """Read a value from the bridge."""
        v = context.get(name)
        return default if v is None else v

    def call(name, *args):
        """Call any registered function (Python or C/Java/JS stub)."""
        if not context.has_function(name):
            raise NameError(...)
        return context.call(name, *args)

    def store_object(obj) -> int:  return context.store_object(obj)
    def load_object(handle): return context.load_object(handle)
    def delete_object(handle):     context.delete_object(handle)

    # ── Build the execution environment ──
    env = {k: v for k, v in context.all().items()}  # All existing bridge values
    env["export"]          = export
    env["export_function"] = export_function
    env["export_class"]    = export_class
    env["get_global"]      = get_global
    env["call"]            = call
    env["store_object"]    = store_object
    env["load_object"]     = load_object
    env["delete_object"]   = delete_object

    original_keys = set(env.keys())  # Remember what existed before

    exec(code, env, env)             # ← RUN THE USER'S PYTHON CODE

    # ── Auto-export new variables created in the block ──
    for key, value in env.items():
        if key.startswith("__") or key in _skip:      continue
        if callable(value) and key not in exports:    continue
        if key in original_keys and key not in exports: continue
        if key not in exports:
            context.set(key, value)
            exports[key] = value

    return exports
```

### How Python Block Sees Its Environment

When a Python block runs, it sees these as built-in names:

| Name | What it does |
|------|-------------|
| `export("name", value)` | Share a value with future blocks |
| `export_function("name", fn)` | Register a Python function |
| `export_class("name", cls, fields)` | Register a class schema |
| `get_global("name")` | Read a value from the bridge |
| `call("name", *args)` | Call any function from any language |
| `store_object(obj)` | Store a Python object, get back a handle |
| `load_object(handle)` | Get an object back by its handle |
| `app_name`, `version`, etc. | All global bridge values — available directly |

---

## FILE 18 — `languages/__init__.py` (Language Registry)

> **Role:** Maps language name strings (like `"c"`, `"python"`) to their runner functions.

### Full Code

```python
from .python_lang import run as python_run
from .runner      import run as _compiled_run

def _make_run(lang):
    def _run(code, context):
        return _compiled_run(lang, code, context)
    return _run

LANGUAGE_REGISTRY = {
    "python":     python_run,
    "javascript": _make_run("javascript"),
    "js":         _make_run("javascript"),  # alias
    "c":          _make_run("c"),
    "c++":        _make_run("cpp"),
    "cpp":        _make_run("cpp"),         # alias
    "java":       _make_run("java"),
}
```

### How the Interpreter Uses This

```python
runner = LANGUAGE_REGISTRY.get("c")  # Gets the C runner function
result = runner(code, context)        # Runs the code
```

---

## FILE 19 — `languages/templates/` (Bridge Glue Code)

> **Role:** Each template file provides helper functions/macros that the user's code can call to export values or call Python functions.

### Templates Overview

| File | Language | Key helpers it provides |
|------|----------|------------------------|
| `c_bridge.h` | C | `export_value(name, val)`, `poly_call(fn, args)` macros |
| `cpp_bridge.hpp` | C++ | `polybridge::export_value(name, val)`, C++ stream based |
| `js_bridge.js` | JavaScript | `poly_export(name, val)`, `get_global(key)`, `__poly_exports` obj |
| `java_bridge.java` | Java | `export_value(String name, ...)`, `poly_call(name, args)` |

These templates are **prepended** to the user's code before compilation/execution, giving the user's code access to the export and bridge-call functions.

---

## 📝 EXAMPLE FILE BREAKDOWN — `example/01_globals.poly`

> This is the simplest example. Great to trace through first.

```poly
global {
    app_name   = "PolyBridge"
    version    = 2
    pi         = 3.14159
    debug_mode = True
}
python {
    print(f"[Python] app_name = {app_name}")
    print(f"[Python] via get_global: {get_global('app_name')}")
}
javascript {
    console.log("[JS] app_name = " + get_global("app_name"));
}
c {
    int main() {
        printf("[C] app_name = %s\n", app_name);
        return 0;
    }
}
```

**What happens when you run it:**

```
poly example/01_globals.poly
         │
         ▼
poly.py reads the file → parse() → ProgramNode with 5 blocks
         │
         ▼
interpret():
  Block 1: global {}
    → process_global() → context.set("app_name", "PolyBridge") etc.

  Block 2: python {}
    → python_lang.run() → exec() with env containing app_name etc.
    → print statements execute

  Block 3: javascript {}
    → runner.run("javascript", code, context)
    → inject_js_globals → "globalThis['app_name'] = 'PolyBridge';"
    → node -e "...full_js..."
    → console.log output appears

  Block 4: c {}
    → runner.run("c", code, context)
    → inject_c_globals → "static const char* app_name = "PolyBridge";"
    → compile with gcc → run ./main.exe
    → printf output appears
```

---

## 📝 EXAMPLE FILE BREAKDOWN — `example/13_full_pipeline.poly`

> This is the best example to study — it shows every language passing data forward.

```
global { raw_value=87, max_value=100, ... }
         ↓ (globals loaded into bridge)
python { normalize the value, export "normalized", "is_valid" }
         ↓ (bridge now has: normalized, is_valid, py_note)
javascript { calculate pct%, build label string, export "pct_str", "label" }
         ↓ (bridge now has: pct_str, label)
c { calculate score = normalized * 1000, export "score" }
         ↓ (bridge now has: score)
cpp { look up score, assign "tier" (GOLD/SILVER etc.), export "tier", "is_premium" }
         ↓ (bridge now has: tier, is_premium)
java { build final report string from all values, export "final_report" }
         ↓ (bridge now has: final_report, report_score, report_tier)
python { read final_report from bridge and print summary }
```

**Data flows forward through the bridge — each language adds to it.**

---

## 🔑 CRITICAL CONCEPTS SUMMARY (Quick Reference for Exam)

### 1. The `.poly` file syntax
```
language_name {
    // code in that language
}
```
- Comments: `//` or `#`
- Blocks can be nested inside `parallel { }` to run concurrently

### 2. How a value travels Python → C
```
Python exports "score" = 870
  → context.set("score", 870)
  → bridge.registry.values["score"] = 870

C block runs:
  → inject_c_globals() reads registry.values
  → generates: "static const long long score = 870;"
  → prepended to C code before compilation
  → C code uses `score` as a normal variable
```

### 3. How a value travels C → Python
```
C code executes:
  export_value("result", 42);
  → prints: "__POLY_EXPORT__|result|int|42"

run_subprocess() reads this line:
  → parse_export_standard() parses it → {"result": 42}
  → returned as exports dict

interpreter.py:
  → context.set("result", 42)
  → bridge now has result = 42
```

### 4. How a Python function is called from JS/C/Java
```
Python block:    export_function("add", lambda a,b: a+b)
                 → registered in bridge as FunctionEntry(func=<lambda>)

JS/C/Java code:
  → poly_call("add", [3, 4])
  → prints: "__POLY_CALL__|add|[3,4]"

run_subprocess() reads this:
  → context.call("add", 3, 4)
  → dispatcher → entry.func(3, 4) → 7
  → encode_return(7) → "__POLY_RET__|int|7"
  → writes to subprocess stdin

JS/C/Java receives: "__POLY_RET__|int|7"
  → decodes as 7
```

### 5. The parallel block
```
parallel {
    python { ... }     ← Runs at the SAME TIME in a thread
    c { ... }          ← Runs at the SAME TIME in a thread
    java { ... }       ← Runs at the SAME TIME in a thread
}
```
Uses Python's `ThreadPoolExecutor` to run blocks concurrently.

---

## 🗺️ COMPLETE ARCHITECTURE FLOWCHART

```
┌─────────────────────────────────────────────────────────────────────┐
│                      user types: poly myfile.poly                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │      poly.py        │
                    │  main()             │
                    └──────────┬──────────┘
                               │ reads file
                    ┌──────────▼──────────┐
                    │   core/parser.py    │
                    │   parse(source)     │
                    └──────────┬──────────┘
                               │ returns
                    ┌──────────▼──────────────┐
                    │  ProgramNode            │
                    │  ├─ BlockNode("global") │
                    │  ├─ BlockNode("python") │
                    │  ├─ BlockNode("c")      │
                    │  └─ ParallelNode(...)   │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────┐
                    │core/interpreter.py  │
                    │  interpret(program) │
                    │  creates Context    │
                    └──────────┬──────────┘
                               │ for each block:
          ┌────────────────────┼─────────────────────────┐
          │                    │                          │
  ┌───────▼────────┐  ┌───────▼────────┐     ┌──────────▼──────────┐
  │ global block   │  │ python block   │     │ C/C++/Java/JS block │
  │                │  │                │     │                     │
  │process_global()│  │python_lang.run()    │runner.run(lang,...)  │
  │parses key=val  │  │exec(code, env) │     │                     │
  │context.set(...)│  │returns exports │     │1. inject globals    │
  └────────────────┘  └───────┬────────┘     │2. read template     │
                              │              │3. write temp file   │
                              │              │4. compile (if C/C++ │
                              │              │   /Java)            │
                              │              │5. run subprocess    │
                              │              │6. protocol.py reads │
                              │              │   stdout markers    │
                              │              │7. return exports    │
                              │              └──────────┬──────────┘
                              │                         │
                              └────────────┬────────────┘
                                           │
                                  ┌────────▼────────┐
                                  │    BRIDGE       │
                                  │  (FunctionReg)  │
                                  │  values dict    │
                                  │  functions dict │
                                  └─────────────────┘
```

---
*This study guide covers every file, concept, data flow, and interaction in the Phase-2 Polyglot Runtime Framework.*
