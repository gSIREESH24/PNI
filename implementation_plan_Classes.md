# Cross-Language Function & Class Bridge — Phase 3 Plan

## ✅ Decisions Locked In
| Question | Answer |
|---|---|
| C/C++ HTTP vs stdin? | **stdin/stdout pipe protocol** — no extra deps |
| Where to start? | **Milestone 2** — Python fn → JS/C/C++/Java |
| Class strategy? | **Schema-based** (struct/class code-gen) — later |

## 🧠 Current State (What Exists)

| Feature | Status |
|---|---|
| Variable export (Python → any) | ✅ Done |
| Variable export (JS/C/C++/Java → Python) | ✅ Done via `__POLY_EXPORT__` markers |
| Python function → Python call | ✅ Done (`export_function` + `call`) |
| Python function → JS/C/C++/Java call | ❌ Not possible (subprocess, no in-process access) |
| JS/C/C++/Java function → Python call | ❌ Not possible |
| Class/Object sharing across languages | ❌ Not done (only handle-based Python-to-Python) |

The **core problem**: JS, C, C++, Java all run as **separate subprocesses** spawned by Python. They cannot directly call Python functions at runtime. The bridge today is **one-directional** — Python pushes values in, subprocess languages push values back via stdout markers.

---

## 🗺️ The Architectural Problem

```
┌─────────────────── Python Process ──────────────────┐
│  PolyBridge  (registry, store, dispatcher)          │
│  Python blocks: direct exec() ← ✅ can call/export │
│                                                     │
│  JS block  →  node -e "..."  (child process)        │
│  C block   →  gcc + ./main.exe (child process)      │
│  C++ block →  g++ + ./main.exe (child process)      │
│  Java block → javac + java Main (child process)     │
└─────────────────────────────────────────────────────┘
```

Child processes **cannot call back into Python** natively. The solution is to make Python **act as an HTTP/IPC server** during subprocess execution, so subprocesses can call it.

---

## 🏗️ Proposed Architecture: The Function Call Server

### The Core Idea

When a subprocess language needs to call a bridge function, it sends an **HTTP request** to a lightweight Python server that the bridge starts, waits for the result, and resumes.

```
┌─────────────────────────────────────────────────────────┐
│  Python Process                                         │
│  ┌─────────────┐       starts       ┌────────────────┐ │
│  │  Interpreter│ ────────────────►  │ BridgeServer   │ │
│  │             │                    │ (localhost:PORT)│ │
│  └─────────────┘                    └────────┬───────┘ │
│                                              │  calls  │
│       PolyBridge ◄───────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
         ▲  HTTP POST /call
         │  {"name": "add", "args": [1, 2]}
┌────────┴────────────┐
│  JS/C/C++/Java      │
│  subprocess         │
│  (child process)    │
└─────────────────────┘
```

---

## 📋 Milestones

### ✅ MILESTONE 1 (Already Done) — Python → Python
`export_function("add", add)` → `call("add", 10, 20)` in next Python block.

---

### 🔲 MILESTONE 2 — Python function → Other Languages (Read-Only Call)

**Goal**: JS/C/C++/Java can **call a Python function** and get the return value.

**How**: 
1. Before running any subprocess block, the interpreter starts a `BridgeServer` (a tiny `http.server` thread on `localhost:PORT`).
2. The server exposes a `POST /call` endpoint that reads `{"name": "add", "args": [1, 2]}`, calls the registered Python function, and returns `{"result": 30}` as JSON.
3. Each language adapter injects a `call_bridge(name, ...args)` helper into the subprocess that does an HTTP POST.

#### The Pipe Protocol

All subprocess languages communicate via **stdin/stdout markers** — same idea as `__POLY_EXPORT__` but for function calls:

```
Subprocess → Python (stdout):
  __POLY_CALL__|<name>|<json_array_of_args>\n

Python → Subprocess (stdin):
  __POLY_RET__|<type>|<value>\n
  where type ∈ { int, float, bool, str, null }
```

The Python side switches from `subprocess.run()` → `subprocess.Popen()` and processes stdout **line-by-line** interactively.

#### Files to Add/Modify:

| File | Action | What changes |
|---|---|---|
| `bridge/pipe_runner.py` | **NEW** | Shared interactive Popen loop with protocol handler |
| `languages/js_lang.py` | **MODIFY** | Inject `call_bridge()` (uses `fs.readSync` for sync stdin); switch to `run_interactive()` |
| `languages/c_lang.py` | **MODIFY** | Inject `call_bridge_i/f/b/s()` helpers + unbuffer stdout; switch to `run_interactive()` |
| `languages/cpp_lang.py` | **MODIFY** | Inject `call_bridge<T>()` template + named wrappers; switch to `run_interactive()` |
| `languages/java_lang.py` | **MODIFY** | Inject `call_bridge()` via `BufferedReader(System.in)`; switch to `run_interactive()` |

#### User Syntax after implementation:
```poly
python {
    def square(x):
        return x * x
    export_function("square", square)
}

javascript {
    let r = call_bridge("square", 9);   // → 81
    console.log("[JS] square(9) =" , r);
}

c {
    int main() {
        long long r = call_bridge_i("square", "[9]");
        printf("[C] square(9) = %lld\n", r);
        return 0;
    }
}

cpp {
    int main() {
        long long r = call_bridge_i("square", "[9]");   // or call_bridge<long long>(...)
        std::cout << "[C++] square(9) = " << r << std::endl;
    }
}

java {
    class Main {
        public static void main(String[] args) {
            Object r = call_bridge("square", 9);
            System.out.println("[Java] square(9) = " + r);
        }
    }
}
```

#### Per-language `call_bridge` injection detail:

| Language | Sync stdin method | Args format |
|---|---|---|
| JS | `fs.readSync(0, buf, 0, 1, null)` byte-by-byte loop | `JSON.stringify([a, b, ...])` |
| C | `fgets(line, size, stdin)` + `setvbuf` unbuffer | manual `"[val]"` string |
| C++ | Same as C + `template<typename R>` return type | manual `"[val]"` string |
| Java | `BufferedReader(System.in).readLine()` | auto-built JSON via `StringBuilder` |

---

### 🔲 MILESTONE 3 — Any Language → Any Language Function Call

**Goal**: JS/C/C++/Java can **register** functions too, and Python (or other blocks) can call them.

**How**:
- JS: register via `poly_export_function("name", fn)` → sends `POST /register_function` with the function's **JS source code snippet**.
- Bridge stores a **"call stub"** for the function — when Python calls it, it re-runs the JS subprocess with just that function + args and gets the result.
- This is a "lazy invoke" pattern (compile the function on demand).

#### New things needed:
| Component | Description |
|---|---|
| `bridge/function_stub.py` | **NEW** — stores function source + language for re-invocation |
| `bridge/bridge_server.py` | Add `POST /register_function` endpoint |
| `bridge/dispatcher.py` | Handle subprocess function stubs, not just in-process callables |
| `languages/js_lang.py` | Inject `poly_export_function()` helper |
| `languages/c_lang.py` | Add `export_function_c()` macro that sends source to server |

---

### 🔲 MILESTONE 4 — Class / Object Sharing

**Goal**: A class defined in one language can be instantiated in another.

**Two strategies:**

#### Strategy A — Schema-Based (Recommended for MVP)
- Python class gets serialized as a **JSON schema** (field names + types).
- Other languages get a matching `struct` (C/C++) or `class` (Java/JS) auto-generated.
- Values flow via the bridge as plain dicts/maps.

```poly
python {
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    export_class("Point", Point, fields={"x": "float", "y": "float"})
}

javascript {
    let p = new Point(3.0, 4.0);    // auto-generated class from schema
    console.log(p.x, p.y);
}

java {
    Point p = new Point(3.0, 4.0);  // auto-generated Java class
    System.out.println(p.x + " " + p.y);
}
```

#### Strategy B — Handle + Method Proxy (Rich OOP)
- Object lives in Python only (stored in `ObjectStore`).
- Other languages hold an **opaque handle**.
- Calling a method = `call_method(handle, "method_name", args)` → HTTP call → Python executes the real method → returns result.

---

## 🔧 Implementation Order (Recommended)

```
Phase 3A  ─→  BridgeServer (HTTP backbone) - IMPLEMENTED via Pipe Protocol
Phase 3B  ─→  Milestone 2 (Python fn → JS/C/C++/Java call) - IMPLEMENTED
Phase 3C  ─→  Milestone 3 (JS/C fn → Python call via stub) - IMPLEMENTED
Phase 3D  ─→  Milestone 4A (Class schema export, struct/class gen) - UP NEXT
Phase 3E  ─→  Milestone 4B (Handle + method proxy, full OOP) - UP NEXT
```

---

## 🏗️ Phase 3D Detailed Plan: Schema-Based Class Export

**Goal**: Python defines a data class schema. The bridge generates native `class` or `struct` definitions in JS, C, C++, and Java so users get native intellisense and strongly-typed objects. We also generate serialization helpers so they can be passed around.

### Core Additions:
1. **`bridge/registry.py`**: Add a `class_schemas` dict.
   ```python
   def export_class_schema(name: str, fields: dict[str, str])
   # e.g., export_class_schema("Point", {"x": "float", "y": "float"})
   ```
2. **`languages/js_lang.py`**:
   Generate ES6 classes:
   ```javascript
   class Point { constructor(x, y) { this.x = x; this.y = y; } }
   globalThis.Point = Point;
   ```
3. **`languages/c_lang.py`**:
   Generate C structs:
   ```c
   typedef struct { double x; double y; } Point;
   // And generate an export macro:
   #define export_value_Point(name, obj) printf("__POLY_EXPORT__%s|json|{\"x\":%f,\"y\":%f}\n", name, obj.x, obj.y);
   ```
4. **`languages/cpp_lang.py`**:
   Generate C++ structs:
   ```cpp
   struct Point { double x; double y; };
   // And an export_value overload
   inline void export_value(const std::string& name, const Point& obj) { ... }
   ```
5. **`languages/java_lang.py`**:
   Generate static nested classes inside `Main`:
   ```java
   public static class Point { public double x; public double y; }
   ```

When objects of these classes are exported via the bridge, they will be serialized as standard JSON dictionaries (`{"x": 1.0, "y": 2.0}`).

---

## 🏗️ Phase 3E Detailed Plan: Object Handles & Method Proxying

Data schemas (Phase 3D) are great for state, but what about objects with **behavior** (methods, network calls, DB connections)? 
We will extend the Phase 2 `ObjectStore` with cross-language RPC.

**Goal**: A Python object is stored in the host process. Subprocesses get a lightweight "proxy" object that forwards method calls back to Python over the stdin/stdout pipe.

### Core Additions:
1. **Pipe Protocol Extension**:
   ```
   Subprocess → Python (stdout):
     __POLY_METHOD__| <handle_id> | <method_name> | <json_args> \n
   ```
2. **`bridge/pipe_runner.py`**:
   Intercept `__POLY_METHOD__|` and call `context.call_method(handle, method, args)`. Return the result via `__POLY_RET__|`.
3. **Language Adapters**:
   When Python exports an object reference to the bridge (e.g., `{"__handle__": "my-db-123"}`), the language adapters automatically wrap it.
   - **JS**: Use JS `Proxy` object to trap method calls.
   - **Python**: Already done natively.
   - **C/C++/Java**: We explicitly inject a `call_method(handle_str, "method", args)` helper so users can invoke methods on remote Python objects.

---

> [!NOTE]
> **User Review Required**:
> Do you approve this approach for Phase 3D and 3E? 
> - **3D** will use code generation to create static types in C/C++/Java based on Python schema definitions.
> - **3E** will build upon our Pipe Protocol to allow calling methods on live Python objects from subprocesses.
