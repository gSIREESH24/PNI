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
Phase 3A  ─→  BridgeServer (HTTP backbone)
Phase 3B  ─→  Milestone 2 (Python fn → JS/C/C++/Java call)
Phase 3C  ─→  Milestone 3 (JS/C fn → Python call via stub)
Phase 3D  ─→  Milestone 4A (Class schema export, struct/class gen)
Phase 3E  ─→  Milestone 4B (Handle + method proxy, full OOP)
```

---

## 📁 Proposed New Files

```
Phase_2_PLF/
├── bridge/
│   ├── bridge_server.py      ← NEW: HTTP server (localhost) for function calls
│   ├── function_stub.py      ← NEW: stores source + lang for subprocess fns
│   ├── class_registry.py     ← NEW: stores class schemas for cross-lang gen
│   ├── dispatcher.py         ← MODIFY: handle stubs + in-process functions
│   ├── poly_bridge.py        ← MODIFY: add start_server/stop_server
│   └── registry.py           ← MODIFY: support stub functions
│
├── languages/
│   ├── js_lang.py            ← MODIFY: inject call_bridge(), poly_export_function()
│   ├── c_lang.py             ← MODIFY: inject call_bridge_int/str/double()
│   ├── cpp_lang.py           ← MODIFY: inject call_bridge() polymorphic fn
│   └── java_lang.py          ← MODIFY: inject callBridge() via HttpURLConnection
│
├── core/
│   └── interpreter.py        ← MODIFY: start/stop server per subprocess block
│
└── example/
    ├── 15_py_fn_to_js.poly   ← NEW example
    ├── 16_py_fn_to_c.poly    ← NEW example
    ├── 17_js_fn_to_python.poly ← NEW example
    └── 18_class_bridge.poly  ← NEW example
```

---

## 🔑 Key Design Decisions

> [!IMPORTANT]
> **HTTP vs Named Pipes vs Stdin/Stdout?**
> HTTP (`localhost`) is chosen because:
> 1. Works on all platforms (Windows + Linux)
> 2. No extra deps (Python's `http.server` is stdlib)
> 3. JSON naturally serializes args/return values
> 4. Synchronous call pattern is simple to implement in all 4 subprocess languages

> [!WARNING]
> **C and C++ require libcurl** (or raw POSIX sockets) for HTTP calls. On Windows, `libcurl` needs to be installed. Alternative: use **stdin/stdout pipe protocol** for C/C++ to avoid the curl dependency entirely.

> [!NOTE]
> **Classes in Phase 3D** will be Schema-based first (Strategy A). Full method proxy (Strategy B) is complex and can come after.

---

## Open Questions

1. **C/C++ HTTP**: Use `libcurl`? Or use a simpler stdin/stdout "function call protocol" to avoid extra dependencies?
2. **JS HTTP**: Node.js has built-in `http` module. Use `fetch()` or `http.request()`?
3. **Starting point**: Do you want Milestone 2 first (Python fn → subprocess) or jump to a specific milestone?
4. **Classes**: Start with Schema-based (struct/class gen) or Handle+proxy?
