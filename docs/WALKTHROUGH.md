# 📖 Polyglot Language Framework — Technical Walkthrough

## What It Is
The Polyglot Language Framework lets you run Python, JavaScript, C, C++, and Java blocks from a single script (`.poly` file) while seamlessly sharing state and calling functions natively across language boundaries.

---

## 🛠️ The Architecture Stack

### 1. The Bridge (`bridge/`)
The **Bridge** connects all pieces. Languages never talk directly to each other; they all funnel their values and remote procedure calls through the Python `Bridge` object.
- `bridge.py`: Main API. Combines routing, memory, and dispatching.
- `protocol.py`: Low-level bidirectional `stdin`/`stdout` JSON parser which listens for `__POLY_CALL__` and writes `__POLY_RET__`.
- `function_registry.py`: Stores the lookup table mapping `"js_multiplier"` to JavaScript background executions, and Python scalars (`x = 10`) for injection.
- `object_store.py`: Converts rich Python objects into opaque Integer Handles which are safe to route across pipelines.
- `stub_runner.py`: A unique executor that "wakes up" sleep-state functions registered in native languages (Universal Vice-Versa calling).

### 2. The Language Templates (`languages/`)
The project utilizes a clean **Template Engine Pattern** avoiding messy string interpolation.
- Languages are managed through `languages/adapters.py` which provides the precise instructions for compiling and calling Node, GCC, and Javac.
- Rather than injecting complicated Python strings, the framework concatenates raw `.h`, `.js`, and `.java` boilerplate skeletons directly from `languages/templates/`. This guarantees full IDE support and formatting.

### 3. The Coordinator (`core/`)
- `parser.py` safely shreds user `.poly` files along bracket `{...}` boundaries.
- `interpreter.py` iteratively evaluates the blocks and actively synchronizes global exports immediately after each block completes.

---

## 🚦 Life Cycle of a Block Execution

Say you run a `c { ... }` block inside your `.poly` script:

1. **Injection:** The `Runner` queries the `FunctionRegistry` for all globally shared attributes. It wraps them as strongly-typed static literals (`static const long long x = 10;`).
2. **Templating:** It concatenates `injections + templates/c_bridge.h + user_c_code`.
3. **Compilation:** It stores the code safely into the OS Temp directory (`C:\Users\...AppData\Local\Temp\plf_c_xxx`) and shells out to `gcc`. No intermediate `.exe` files litter your primary directory.
4. **Execution Protocol:** It runs the compiled binary through `protocol.run_subprocess()`.
5. **Collection:** Standard console output (`printf("Hello");`) is displayed to the user normally. Outputs prefixed with `__POLY_EXPORT__` are caught by the parser and safely dumped into the `Bridge` to share with the next executing block.
6. **Cleanup:** Python deletes the OS Temp workspace immediately.

---

## 🪝 Available Bridge Hooks

These exact commands are syntactically wired into C, C++, JavaScript, Java, and Python environments:

- `export(name, val)` / `poly_export()`: Injects numbers or strings back into the Central Bridge.
- `export_function(name, func)`: Submits a live callable to the Registry for later use by other processes.
- `get_global(name)`: Retrieves dynamically injected memory variables.
- `call_bridge(name, ...args)` / `context.call()`: Tells the Bridge Dispatcher to blindly execute a stored function anywhere in the polyglot stack and await its return.

For concrete coding examples illustrating these hooks working across language borders, please reference the [example/README.md](../example/README.md) suite!
