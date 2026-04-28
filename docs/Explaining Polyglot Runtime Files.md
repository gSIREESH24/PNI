# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

I am not getting why different files were  even there  explain every files with example why they used

### Planner Response

Let me first explore your project structure to give you accurate explanations.

*Listed directory [Phase_2_PLF](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF) *

*Listed directory [PNI](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI) *

*Listed directory [bridge](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge) *

*Listed directory [core](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core) *

*Listed directory [languages](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages) *

*Listed directory [templates](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/templates) *

*Listed directory [example](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/example) *

### Planner Response

Now let me read all the key source files:

*Viewed [lexer.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core/lexer.py) *

*Viewed [ast.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core/ast.py) *

*Viewed [parser.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core/parser.py) *

*Viewed [context.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core/context.py) *

*Viewed [interpreter.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/core/interpreter.py) *

*Viewed [bridge.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/bridge.py) *

*Viewed [function_registry.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/function_registry.py) *

*Viewed [dispatcher.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/dispatcher.py) *

*Viewed [object_store.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/object_store.py) *

*Viewed [protocol.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/protocol.py) *

*Viewed [stub_runner.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/stub_runner.py) *

*Viewed [value_types.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/value_types.py) *

*Viewed [__init__.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/bridge/__init__.py) *

*Viewed [adapters.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/adapters.py) *

*Viewed [runner.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/runner.py) *

*Viewed [python_lang.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/python_lang.py) *

*Viewed [__init__.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/__init__.py) *

*Viewed [poly.py](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/poly.py) *

*Viewed [01_globals.poly](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/example/01_globals.poly) *

### Planner Response

Now I have everything I need. Let me create a comprehensive, beginner-friendly explanation document.

*Edited relevant file*

### Planner Response

Here's a complete explanation of every file — broken into groups so it's easy to digest.

---

## 🗂️ The Big Picture

Your project is a **Polyglot Runtime** — you write one `.poly` file mixing 5 languages, and the runtime executes them all while sharing data. Every file has a specific role in making that happen.

---

## 🟩 Entry Point (Starting Files)

| File | One-Line Role |
|------|--------------|
| **`poly.py`** | The "Start Button" — reads your `.poly` file, sends it to parser, then to interpreter |
| **`poly.bat`** | Windows shortcut so you can type `poly file.poly` instead of `python poly.py file.poly` |

---

## 🟦 `core/` — Reads & Runs Your `.poly` File

| File | Role | Analogy |
|------|------|---------|
| **`lexer.py`** | Splits source code into lines | Like cutting a book into individual pages |
| **`ast.py`** | Defines `BlockNode` and `ProgramNode` — containers that hold parsed blocks | Like a box that stores "this is Python code, this is C code" |
| **`parser.py`** | Finds each `language { ... }` block and creates `BlockNode` objects | Reads `python { ... }` → stores it as `BlockNode("python", "print(x)")` |
| **`interpreter.py`** | Loops over every block, picks the right runner, executes it | The conductor of the orchestra |
| **`context.py`** | The clean API layer wrapping `Bridge` — what runners use to read/write shared variables | Like a "nice interface" hiding messy internals |

---

## 🟧 `bridge/` — Shared Memory Between Languages

| File | Role | Why Needed |
|------|------|-----------|
| **`bridge.py`** | Central hub — owns the registry, store, and dispatcher | One simple object to rule them all |
| **`function_registry.py`** | The "phone book" — stores variables (`x=42`) and function entries (`add: C stub`) | Without this, no shared memory exists |
| **`dispatcher.py`** | Routes `context.call("add", 5)` — directly calls Python functions OR sends C/Java/JS to the stub runner | Without this, Python can't call C |
| **`object_store.py`** | Stores Python objects, gives a numeric **handle** back — C/JS can reference Python objects via this ticket number | Without this, complex objects can't cross language boundaries |
| **`protocol.py`** | Defines the text format for talking to subprocesses: `__POLY_EXPORT__`, `__POLY_CALL__`, `__POLY_RET__` | C/Java can't export values or call Python back without this |
| **`stub_runner.py`** | Wraps your C/Java/JS function source in a full `main()`, compiles it, runs it, reads the result | Without this, you can't call a C function from Python |
| **`value_types.py`** | Universal type envelope — `PolyValue(type=INT, value=42)` — so the bridge always knows what type it's passing | Centralizes type logic instead of duplicating it everywhere |

---

## 🟨 `languages/` — How to Run Each Language

| File | Role |
|------|------|
| **`__init__.py`** | The language menu — maps `"python" → python_run`, `"c" → runner("c")`, etc. |
| **`python_lang.py`** | Runs Python blocks using `exec()` inline, injects `export()`, `call()`, `get_global()` helpers |
| **`runner.py`** | Generic engine for C/C++/Java/JS: injects globals → writes temp file → compiles → runs subprocess |
| **`adapters.py`** | Config table: each language's file extension, compile command, global injection logic, export parser |

---

## 🟥 `languages/templates/` — Pre-Written Bridge Helpers

Each template file gets **pasted into every generated program** to give it the `poly_export()` function:

| File | What it provides |
|------|----------------|
| **`c_bridge.h`** | `poly_export_int("x", 42)` macro → prints `__POLY_EXPORT__x|int|42` |
| **`cpp_bridge.hpp`** | Same but with `std::cout` and C++ types |
| **`java_bridge.java`** | `poly_export_int(name, val)` static method |
| **`js_bridge.js`** | `poly_export(name, value)` function + `get_global()` |

---

## 🔄 Flow in 7 Steps

```
1. poly.py            → reads file.poly
2. parser.py          → splits into BlockNode list
3. interpreter.py     → loops over each block
4. languages/         → picks right runner
5. adapters.py        → injects globals into source, wraps code
6. runner.py          → compiles & runs as subprocess
7. protocol.py        → reads __POLY_EXPORT__ lines back into shared context
```

The full detailed artifact with **code examples for every single file** is ready to read — check the artifact panel above! 👆

### User Input

in this why we are injectly shared varibles into c/c++/java why not js

### Planner Response

Great question! Let me clear the confusion directly.

---

## JS **IS** Injected — But Differently

All 4 languages get globals injected. The **difference is HOW**, because of a fundamental difference between compiled vs interpreted languages.

---

## The Real Difference

### C / C++ / Java → **Must declare type before compile**

These are **compiled languages**. Before `gcc` or `javac` even runs, every variable must have a declared type in the source code.

```c
// _inject_c_globals() generates this:
static const long long x = 42;
static const char * name = "Alice";
```
```java
// _inject_java_members() generates this:
static final long x = 42L;
static final String name = "Alice";
```

Then in your `.poly` block you just write:
```c
printf("%lld", x);   // x is already declared above ✅
```

---

### JavaScript → **No types needed, just assign at runtime**

JS is **dynamically typed** — no type declarations. So the injection is simpler:

```js
// _inject_js_globals() generates this:
globalThis["x"] = 42;
globalThis["name"] = "Alice";
```

But here's the catch: in Node.js when you run code with `node -e "..."`, variables set on `globalThis["x"]` are **not automatically accessible as bare `x`** in the local scope. So JS uses the helper function instead:

```js
// You write in your .poly block:
console.log(get_global("x"));     // ✅ reads from globalThis
console.log(x);                   // ❌ might be undefined in Node -e context
```

---

## Side by Side in `adapters.py`

```python
ADAPTERS = {
    "c": {
        "inject_globals": _inject_c_globals,    # → static const int x = 42;
        "inject_classes": _inject_c_classes,    # → typedef struct { ... }
    },
    "cpp": {
        "inject_globals": _inject_cpp_globals,  # → static const int x = 42;
        "inject_classes": _inject_cpp_classes,  # → struct MyClass { ... };
    },
    "java": {
        "inject_globals": _inject_java_members, # → static final long x = 42L;
        "inject_classes": None,                 # handled inside inject_java_members
    },
    "javascript": {
        "inject_globals": _inject_js_globals,   # → globalThis["x"] = 42;
        "inject_classes": None,  # ← JS doesn't need class declarations
    },
}
```

---

## Summary Table

| Language | Injection Style | Access in code |
|----------|----------------|----------------|
| **C** | `static const int x = 42;` | `x` directly |
| **C++** | `static const int x = 42;` | `x` directly |
| **Java** | `static final long x = 42L;` | `x` directly |
| **JS** | `globalThis["x"] = 42;` | `get_global("x")` |

**Root reason:** C/C++/Java need the **type tag** (`int`, `long`, `String`) because their compiler demands it. JS has no types, so a simple runtime assignment works — but Node.js's `-e` execution context requires reading it back via `get_global()` instead of bare `x`.

### User Input

explain pillar three in architure.md clearly

### Planner Response

Let me find the `architecture.md` file first.

*Listed directory [docs](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/docs) *

*Viewed [ARCHITECTURE.md](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/docs/ARCHITECTURE.md) *

### Planner Response

Now I have the full context. Let me explain Pillar 3 deeply and clearly.

---

## 🔌 Pillar 3: The Interactive Pipe Protocol — Explained Clearly

**The problem it solves:**

> You're writing C++ code. Mid-execution, you want to call a Python function. **How?** C++ and Python are completely separate processes — they don't share memory. You can't just call `python_func()` from C.

---

## The Core Idea: Walkie-Talkies via stdin/stdout

Instead of complex JNI/binding libraries, this framework uses the **simplest thing every OS has** — standard input and output (stdin/stdout). Every program can print text (`stdout`) and receive text (`stdin`). The framework uses that as a **communication channel**.

Think of it like two people talking via walkie-talkie:
- C++ **speaks** (prints to stdout) → Python **listens** (reads stdout)
- Python **responds** (writes to stdin) → C++ **reads** (reads stdin)

---

## Step-by-Step Walkthrough

### 📝 Your `.poly` file:
```c
python {
    def add(a, b):
        return a + b
    export_function("add", add)
}

c {
    long long result = call_bridge("add", 3, 7);
    printf("Result = %lld\n", result);
}
```

---

### Step 1: Python registers the function

Python's `export_function("add", add)` stores it in the `FunctionRegistry`:
```
Registry["add"] = FunctionEntry(func=<add>, language="python")
```

---

### Step 2: C block starts as a subprocess

`runner.py` compiles the C code and launches it as a **separate child process** using `subprocess.Popen()` in `protocol.py`.

```python
proc = subprocess.Popen(
    ["./main.exe"],
    stdin=subprocess.PIPE,    # Python can send data TO the C process
    stdout=subprocess.PIPE,   # Python can READ what C prints
)
```

Now Python and C are two separate running programs connected by a pipe.

---

### Step 3: C calls `call_bridge()` → Prints a magic string and FREEZES

When the C code hits `call_bridge("add", 3, 7)`, the `c_bridge.h` template has this macro:

```c
// From c_bridge.h template:
#define call_bridge(name, ...) _poly_call(name, __VA_ARGS__)

// Which prints this to stdout and then waits for a response:
printf("__POLY_CALL__|add|[3, 7]\n");
fflush(stdout);
// Now C is FROZEN — blocking on fgets(stdin) — waiting for Python's reply
```

So C literally **prints a text message and stops executing** until Python responds.

---

### Step 4: Python's `run_subprocess()` loop reads it

Inside `protocol.py`, there's a **live reading loop** that watches every line C prints:

```python
for raw in proc.stdout:          # read every line C prints
    line = raw.strip()

    if line.startswith("__POLY_CALL__|"):
        # C is asking us to call a function!
        payload = line[len("__POLY_CALL__|"):]   # "add|[3, 7]"
        fn_name, args_json = payload.split("|", 1)
        # fn_name = "add",  args_json = "[3, 7]"

        args   = json.loads(args_json)           # [3, 7]
        result = context.call(fn_name, *args)    # calls Python's add(3, 7) → 10
        
        # Send result back to C:
        proc.stdin.write("__POLY_RET__|int|10\n")
        proc.stdin.flush()
```

---

### Step 5: Python sends the result back → C unfreezes

C's `fgets(stdin)` gets `__POLY_RET__|int|10\n` and the C template parses it:

```c
// c_bridge.h parses the reply:
// "__POLY_RET__|int|10"  →  returns 10LL
long long result = 10;  // call_bridge() now returns this
printf("Result = %lld\n", result);  // prints: Result = 10
```

---

## The Full Conversation (as text messages)

```
C stdout  →→→→  "__POLY_CALL__|add|[3, 7]"       (C asks Python to run 'add')
                                                  (C is frozen, waiting...)
                ←←←← Python looks up 'add' in registry
                ←←←← Python runs add(3, 7) → gets 10
Python stdin →→→→  "__POLY_RET__|int|10"           (Python replies with 10)
C unfreezes, result = 10
C prints:    "Result = 10"
```

---

## Why `__POLY_CALL__`, `__POLY_RET__`, `__POLY_EXPORT__` — Why These Magic Strings?

Because stdout is **mixed** — C might print normal things too (like debug messages). Python needs to know which lines are **bridge commands** vs normal output. The prefixes act as **signal flags**:

| Magic String | Meaning |
|---|---|
| `__POLY_CALL__\|func\|[args]` | "Hey Python, please call this function" |
| `__POLY_RET__\|type\|value` | "Here is the return value" |
| `__POLY_EXPORT__\|name\|type\|value` | "I'm exporting this variable to the bridge" |
| `__POLY_REGISTER__\|...` | "Register this function stub for later" |

Anything that **doesn't start with these** → Python just prints it to the terminal normally (that's the `else: print(line)` at the end of `protocol.py`).

---

## Why Pipes Instead of JNI or Sockets?

| Approach | Complexity | What it needs |
|---|---|---|
| **JNI** (Java Native Interface) | 🔴 Extremely complex | Custom C headers, JVM setup, pointer management |
| **Sockets/HTTP** | 🟡 Medium | Network setup, serialization, ports |
| **stdin/stdout Pipes** ✅ | 🟢 Super simple | Every OS has this built-in. Just read/write text! |

Pipes are **zero-dependency** — every language (C, Java, JS, Python) can read from stdin and write to stdout. No libraries needed.

---

## One-Line Summary

> **C prints a text message to ask Python for help → Python reads it, executes the function, prints the answer back → C reads that answer and continues.**  
> That's it. The entire cross-language function calling system is just **structured text over stdin/stdout**.

### User Input

what is used to freeze c

### Planner Response

Let me check the actual C bridge template to show you the exact code.

*Viewed [c_bridge.h](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/languages/templates/c_bridge.h) *

### Planner Response

The answer is right there in the source. Here it is:

---

## What Freezes C: `fgets(stdin)`

This is the exact function — **line 33** of `c_bridge.h`:

```c
static void _poly_call_raw(const char *name, const char *args_json) {
    printf("__POLY_CALL__|%s|%s\n", name, args_json);  // Step 1: shout to Python
    fflush(stdout);                                      // Step 2: make sure it's sent immediately
    if (!fgets(__poly_ret_buf, sizeof(__poly_ret_buf), stdin))  // Step 3: FREEZE — wait for reply
        __poly_ret_buf[0] = '\0';
}
```

---

## What Each Line Does

| Line | What it does |
|---|---|
| `printf("__POLY_CALL__\|...")` | Sends the function name + args to Python via stdout |
| `fflush(stdout)` | Forces the message to be sent **right now** (not buffered) |
| `fgets(..., stdin)` | **THIS is the freeze** — C stops here and waits until Python writes a reply to stdin |

---

## Why `fgets` Freezes

`fgets` is a **blocking read** — it means:

> _"Keep waiting on this line until you receive a full line of text from stdin. Don't move forward. Just wait."_

C's execution is literally **stuck** at that `fgets` line until Python sends back `__POLY_RET__|int|10\n`. The moment Python writes that, `fgets` unblocks, reads the line into `__poly_ret_buf`, and C continues running.

---

## The Full Freeze-Unfreeze Cycle

```
C hits call_bridge("add", 3, 7)
  │
  ├─ printf("__POLY_CALL__|add|[3,7]")  ← shouts to Python
  ├─ fflush(stdout)                     ← ensures message is delivered
  └─ fgets(stdin)  ←━━━━━━━━━━━━━━━━━━━━ FROZEN HERE, C is paused
                                         Python reads "__POLY_CALL__..."
                                         Python runs add(3,7) = 10
                                         Python writes "__POLY_RET__|int|10"
  └─ fgets returns  ←━━━━━━━━━━━━━━━━━━━ UNFREEZES, result is in buffer
  └─ _parse_ret_i() reads "10" from buffer
  └─ call_bridge returns 10LL to C code
C continues normally...
```

---

**One-liner:** `fgets(stdin)` freezes C because it is a **blocking I/O call** — C cannot proceed until it receives a complete line of text from Python through the pipe.

### User Input

what is subprocess in this explain

### Planner Response

Great question. Let me explain subprocess from scratch using your own project's code.

---

## What is a Subprocess?

> A **subprocess** is a **child program that your main Python program launches and controls**.

Think of it like a **boss and a worker**:
- **Python (boss)** = the main process, always running
- **C/Java/JS (worker)** = a separate program Python starts, uses, then closes

---

## Why Does This Project Need Subprocesses?

Python **cannot directly run** C, Java, or JavaScript code inside itself. These are totally different languages with different runtimes:

| Language | Needs |
|---|---|
| C | Compiled by `gcc`, runs as `.exe` |
| Java | Compiled by `javac`, runs in JVM |
| JavaScript | Runs inside `node.exe` |

Python can't "become" gcc or node. So instead, Python **launches them as separate programs** — that's a subprocess.

---

## Where It Happens in Your Code

**`runner.py`** — this is where Python spawns the subprocess:

```python
import subprocess

# For C: compile first
subprocess.run(["gcc", "main.c", "-o", "main.exe"])  # compile

# Then run as subprocess
proc = subprocess.Popen(
    ["./main.exe"],         # ← launch the compiled C program
    stdin=subprocess.PIPE,  # ← Python can WRITE to C's input
    stdout=subprocess.PIPE, # ← Python can READ C's output
    stderr=subprocess.PIPE  # ← Python can READ C's errors
)
```

**`protocol.py`** — this is where Python talks to that subprocess:

```python
for raw in proc.stdout:      # read every line C prints
    line = raw.strip()
    
    if line.startswith("__POLY_CALL__|"):
        # C is calling a Python function
        result = context.call(fn_name, *args)
        proc.stdin.write(encode_return(result))  # send answer back
```

---

## Real Example — What Happens When You Run a C Block

```
global {
    x = 10
}
c {
    printf("x = %lld\n", x);
}
```

**Step by step:**

```
1. Python starts (the MAIN process)
   PID: 1000

2. Python reads the C block code

3. Python calls runner.py → writes "main.c" to temp folder
   File: C:\Temp\plf_c_abc123\main.c

4. Python runs:
   subprocess.run(["gcc", "main.c", "-o", "main.exe"])
             ↑
         This IS a subprocess!  (gcc itself runs as PID: 1001)
         Python waits for it to finish

5. Python runs:
   proc = subprocess.Popen(["main.exe"])
                  ↑
         Another subprocess! (main.exe runs as PID: 1002)
         Python and main.exe are now TWO programs running simultaneously

6. main.exe prints:  "x = 10"
   Python reads that from proc.stdout

7. main.exe exits → subprocess ends → Python continues
```

---

## The Process Tree (Visual)

```
python poly.py script.poly        ← MAIN PROCESS (always alive)
│
├── gcc main.c -o main.exe        ← SUBPROCESS 1 (compile, then dies)
│
├── ./main.exe                    ← SUBPROCESS 2 (runs C code)
│     │
│     │  stdout pipe → Python reads this
│     │  stdin pipe  ← Python writes to this
│     │
│     └── exits when done
│
├── node -e "..."                 ← SUBPROCESS 3 (runs JS code)
│
└── java -cp . Main               ← SUBPROCESS 4 (runs Java code)
```

Python is the **parent**. All others are **children**.

---

## `subprocess.Popen` vs `subprocess.run` — What's the Difference?

Your project uses **both**:

| | `subprocess.run()` | `subprocess.Popen()` |
|---|---|---|
| **Used for** | Compile step (gcc, javac) | Running the compiled program |
| **Behaviour** | Wait until it finishes, then continue | Start it and **talk to it live** |
| **In your code** | `subprocess.run(["gcc", ...])` | `subprocess.Popen(["./main.exe"], stdin=PIPE, stdout=PIPE)` |
| **Why** | Compilation must finish before running | C/Java need live back-and-forth communication with Python |

---

## The Key Point: Pipes Connect Them

Without `stdin=PIPE, stdout=PIPE`, the subprocess would just print to your terminal and Python couldn't read it. The pipes turn stdout/stdin into **a private communication channel between Python and the subprocess**.

```
Normal program:    main.exe → prints to YOUR TERMINAL
With PIPE:         main.exe → prints to Python's buffer → Python reads it
```

---

## One-Line Summary

> A **subprocess** in this project is a **C/Java/JS program that Python launches, controls, and communicates with through stdin/stdout pipes** — because Python can't run those languages directly inside itself.

### User Input

what dispatcher doing here

### Planner Response

## What Dispatcher Does — Explained Simply

---

## One Line Answer

> **Dispatcher is the traffic cop** — when someone calls `context.call("add", 5, 3)`, the Dispatcher decides **WHO should handle it and HOW**.

---

## The Full Code (Only 36 Lines)

```python
class Dispatcher:

    def __init__(self, registry: FunctionRegistry):
        self._registry = registry

    def call(self, name, *args, context=None):
        entry = self._registry.get_function(name)   # Step 1: Look it up

        if entry is None:
            raise NameError(f"Function '{name}' is not registered.")

        if entry.func is not None:                  # Step 2a: Python function?
            return entry.func(*args)                #   → call it directly

        if entry.stub_source is not None:           # Step 2b: C/Java/JS function?
            return stub_runner.invoke(...)          #   → compile & run it
        
        raise RuntimeError("No callable and no stub source.")
```

**That's its entire job** — 2 decisions.

---

## The Two Paths Dispatcher Chooses Between

### Path A — Python Function (direct call)

```
context.call("add", 5, 3)
       ↓
Dispatcher looks up "add" in registry
       ↓
Finds:  entry.func = <python lambda>   ← func exists!
       ↓
Just calls:  entry.func(5, 3)   → returns 8
       ↓
Done. No subprocess, no compiling.
```

**Example that triggers Path A:**
```python
# In your .poly file:
python {
    def add(a, b):
        return a + b
    export_function("add", add)
}
c {
    long long r = call_bridge_i("add", "[5, 3]");   ← calls Python's add
}
```

---

### Path B — C / Java / JS Function (stub runner)

```
context.call("square", 7)
       ↓
Dispatcher looks up "square" in registry
       ↓
Finds:  entry.func = None             ← no Python callable
        entry.stub_source = "int square(int x){ return x*x; }"  ← C code!
       ↓
Sends to stub_runner.invoke(...)
  → wraps in main(), compiles with gcc, runs, reads result
       ↓
Returns 49
```

**Example that triggers Path B:**
```python
# In your .poly file:
c {
    export_bridge_function("square", "int square(int x){ return x*x; }", "int");
}
python {
    result = call("square", 7)   ← Python calling C's square!
    print(result)                # prints 49
}
```

---

## Why Is Dispatcher Separate? Why Not Put This Logic in Bridge?

Because of **Single Responsibility** — each class does ONE thing:

```
FunctionRegistry  → only STORES functions (the phone book)
Dispatcher        → only ROUTES calls    (the operator)
Bridge            → only COORDINATES     (the manager)
```

If you put routing logic inside the registry, the registry would need to know about `stub_runner`, subprocesses, compilers — it would become a 500-line mess.

---

## Visual Summary

```
context.call("add", 5, 3)
         │
         ▼
    Dispatcher.call()
         │
         ├── Look up "add" in FunctionRegistry
         │
         ├── Is entry.func set?  ──YES──► call entry.func(5, 3)  → done
         │
         └── Is entry.stub_source set?  ──YES──► stub_runner.invoke()
                                                      │
                                          compile + run as subprocess
                                                      │
                                                 return result
```

---

## One-Line Summary

> Dispatcher answers one question: **"This function was asked for — is it a Python function I can call directly, or is it a C/Java/JS stub I need to compile and run?"**

### User Input

explain pillar with all these

### Planner Response

## All 5 Pillars — With Everything Connected

---

## 🏛️ Pillar 1: The Master Python Process (The Bird's Eye View)

**The Big Idea:** Python is the **permanent boss**. It never dies. Everything else (C, Java, JS) are temporary workers Python creates and destroys.

```
You type:   poly example.poly
                │
                ▼
          poly.py starts
                │
          parser.py reads the .poly file
          splits it into blocks:
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │ global block│  │python block │  │   C block   │
          └─────────────┘  └─────────────┘  └─────────────┘
                │
          interpreter.py loops over each block
                │
          sends each block to Bridge
```

**What each piece does:**

| File | Role in Pillar 1 |
|---|---|
| `poly.py` | Reads the file, calls parse then interpret |
| `parser.py` | Splits `.poly` into `BlockNode` list |
| `interpreter.py` | Loops over blocks, picks the right runner |
| `Bridge` | Central coordinator that owns all shared state |
| `Dispatcher` | Routes function calls to the right handler |
| `FunctionRegistry` | Stores all variables and functions |
| `ObjectStore` | Stores Python objects by handle number |

**Python never stops running** — it's always alive, waiting, reading subprocess output, and routing calls. C/Java/JS are born and die for each block.

---

## 🏛️ Pillar 2: The Template Engine (Sharing Variables)

**The Big Idea:** C, Java, and JS run in **completely separate processes** — they have zero access to Python's memory. So the framework **injects variables directly into the source code** before compiling.

```
Bridge has:  x = 42,  name = "Alice"
                │
                ▼
         adapters.py reads the bridge context
                │
         inject_globals() converts them to that language's syntax
                │
    ┌───────────┴───────────┐
    │ C gets:               │   Java gets:              JS gets:
    │ static const          │   static final            globalThis["x"] = 42;
    │   long long x = 42;   │   long x = 42L;           globalThis["name"] = "Alice";
    │ static const          │   static final
    │   char* name="Alice"; │   String name = "Alice";
    └───────────────────────┘
                │
         runner.py assembles the full source:
         ┌────────────────────────────────────┐
         │  injected globals (variables)       │
         │  + c_bridge.h  (export/call macros) │
         │  + your C code                      │
         └────────────────────────────────────┘
                │
         subprocess.run(["gcc", "main.c", "-o", "main.exe"])
                │
         compiled → ready to run
```

**Why C/Java need type declarations but JS doesn't:**

| Language | Injection Style | Why |
|---|---|---|
| C/C++ | `static const long long x = 42;` | Compiled — must know type before gcc runs |
| Java | `static final long x = 42L;` | Compiled — javac needs type declarations |
| JS | `globalThis["x"] = 42;` | Interpreted — no types needed, just assign at runtime |

**Files involved:**

| File | Role in Pillar 2 |
|---|---|
| `adapters.py` | Has `inject_globals()` for each language |
| `runner.py` | Assembles full source, calls subprocess.run to compile |
| `templates/c_bridge.h` | Pre-written C macros for export/call |
| `templates/cpp_bridge.hpp` | Same for C++ |
| `templates/java_bridge.java` | Same for Java |
| `templates/js_bridge.js` | Same for JS |

---

## 🏛️ Pillar 3: The Interactive Pipe Protocol (Live Function Calling)

**The Big Idea:** After compilation, C/Java/JS runs as a **subprocess**. But what if mid-execution it needs to call a Python function? They use **stdin/stdout pipes as a walkie-talkie**.

```
subprocess.Popen(
    ["./main.exe"],
    stdin  = PIPE,   ← Python can WRITE into C's input
    stdout = PIPE,   ← Python can READ C's output
    stderr = PIPE    ← Python can READ C's errors
)
```

**What freezes C:** `fgets(stdin)` in `c_bridge.h`

```c
// This is _poly_call_raw() in c_bridge.h:

printf("__POLY_CALL__|add|[5,3]\n");   // 1. C shouts to Python
fflush(stdout);                         // 2. Force-send immediately
fgets(__poly_ret_buf, sizeof(...), stdin);  // 3. FREEZE — wait for reply
                                        //    C is stuck here until Python responds
```

**The full live conversation:**

```
C is running...
│
├── hits call_bridge("add", 5, 3)
│       │
│       ├── prints:  "__POLY_CALL__|add|[5,3]"   →→→→ stdout pipe →→→→ Python reads it
│       │
│       └── fgets(stdin)  ← FROZEN                     Python: looks up "add"
│                                                       Python: calls add(5,3) = 8
│                                                       Python: writes "__POLY_RET__|int|8"
│       fgets returns ← UNFREEZES    ←←←←←← stdin pipe ←←←←← Python sends it
│       reads "8" from buffer
│
└── continues... result = 8
```

**The magic strings (why they exist):**

C also prints normal things like `printf("hello")`. Python needs to tell apart **bridge commands** from **normal print output**:

| String | Meaning |
|---|---|
| `__POLY_CALL__\|func\|[args]` | C asking Python: "please call this function" |
| `__POLY_RET__\|type\|value` | Python replying: "here is the return value" |
| `__POLY_EXPORT__\|name\|type\|val` | C saying: "store this variable in the bridge" |
| `__POLY_REGISTER__\|...` | C saying: "register this function stub" |
| anything else | Normal output → just print to terminal |

**Files involved:**

| File | Role in Pillar 3 |
|---|---|
| `templates/c_bridge.h` | Has `_poly_call_raw()` with `printf + fflush + fgets` — the freeze mechanism |
| `bridge/protocol.py` | Has `run_subprocess()` — the Python side reading loop |
| `bridge/dispatcher.py` | Called when `__POLY_CALL__` arrives — routes to the right function |
| `runner.py` | Creates the subprocess with `Popen(stdin=PIPE, stdout=PIPE)` |

---

## 🏛️ Pillar 4: Recursive Vice-Versa Routing

**The Big Idea:** What if **Java wants to call a JavaScript function**? Neither is Python. How does this work?

Answer: **Every non-Python function's source code is saved as a stub**. When someone calls it, Python's `stub_runner` compiles and runs it on-demand as a micro subprocess.

```
JS block runs and registers a function:
   export_bridge_function("multiply", "function(x){ return x*10; }", "int")
            │
            prints: "__POLY_REGISTER__|multiply|js|int|<source>"
            │
   Python reads it → stores in FunctionRegistry:
   functions["multiply"] = FunctionEntry(
       language="javascript",
       stub_source="function(x){ return x*10; }",
       func=None   ← no Python callable!
   )
```

Now Java calls it:

```
Java prints:  "__POLY_CALL__|multiply|[5]"
                    │
            Python reads → Dispatcher.call("multiply", 5)
                    │
            Dispatcher checks:
              entry.func = None          ← no Python function
              entry.stub_source = "..."  ← JS source code exists!
                    │
            → sends to stub_runner.invoke()
                    │
            stub_runner builds a complete JS program:
            ┌──────────────────────────────────────┐
            │ function __stub_fn(x){ return x*10; } │
            │ (function() {                         │
            │   var r = __stub_fn.apply(null, [5]); │
            │   process.stdout.write("__POLY_RET__...) │
            │ })();                                 │
            └──────────────────────────────────────┘
                    │
            subprocess.Popen(["node", "-e", snippet])
                    │
            reads back: "__POLY_RET__|int|50"
                    │
            Python sends "__POLY_RET__|int|50" back to Java
                    │
Java unfreezes, gets 50
```

**The route:**

```
Java subprocess
     └── __POLY_CALL__|multiply|[5]  →→→  Python (protocol.py)
                                              └── Dispatcher
                                                    └── stub_runner
                                                          └── Node.js subprocess
                                                                └── returns 50
                                              └── __POLY_RET__|int|50  ←←←
Java gets 50 ←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

**Files involved:**

| File | Role in Pillar 4 |
|---|---|
| `bridge/dispatcher.py` | Sees `entry.func=None`, routes to `stub_runner` |
| `bridge/stub_runner.py` | Builds complete runnable program, spawns subprocess, reads result |
| `bridge/function_registry.py` | Stores the stub source code in `FunctionEntry.stub_source` |
| `bridge/protocol.py` | Handles `__POLY_REGISTER__` lines — triggers stub registration |

---

## 🏛️ Pillar 5: Global OOP — Object Handles

**The Big Idea:** A Python object (`class Counter`) cannot physically exist inside a Java or C++ process. So the framework gives the object a **numbered ticket (handle)** and keeps the real object safe in Python's `ObjectStore`. Other languages hold only the ticket number and use it to call methods.

```
Python block runs:
   counter = Counter()        ← real Python object in memory
   handle = store_object(counter)  → ObjectStore gives ticket #1
   export("counter_handle", 1)    → bridge stores: counter_handle = 1
```

Other languages get the handle number as a plain integer:

```
C++ gets:    static const long long counter_handle = 1;
Java gets:   static final long counter_handle = 1L;
```

Now Java wants to call `counter.increment()`:

```
Java prints:  "__POLY_METHOD__|1|increment|[]"
                    │
            Python reads it in protocol.py
                    │
            context.call_method(handle=1, method="increment")
                    │
            ObjectStore.get(1) → retrieves the real Python Counter object
                    │
            getattr(counter_obj, "increment")()  ← calls the real method
                    │
            Python sends result back to Java via stdin pipe
                    │
Java unfreezes, counter was incremented in Python's memory
```

**Why handles?** Because a Java `int` (the handle = 1) **can cross any language boundary**. The real object stays safe in Python.

```
ObjectStore:
┌──────────────────────────────────┐
│  handle 1  →  <Counter object>   │
│  handle 2  →  <User object>      │
│  handle 3  →  [1, 2, 3] (list)   │
└──────────────────────────────────┘
C/Java/JS only ever hold: 1, 2, 3
They never touch the real objects.
```

**Files involved:**

| File | Role in Pillar 5 |
|---|---|
| `bridge/object_store.py` | Stores Python objects, gives numeric handles |
| `bridge/protocol.py` | Handles `__POLY_METHOD__` lines from subprocesses |
| `core/context.py` | `store_object()`, `load_object()`, `call_method()` API |
| `bridge/bridge.py` | `call_method()` → loads from store → calls `getattr(obj, method)()` |

---

## All 5 Pillars Connected — The Full Picture

```
┌─────────────────────────────────────────────────────────────────

### Planner Response

## All 5 Pillars — Full Explanation With Everything Connected

---

## 🏛️ Pillar 1: The Master Python Process

**Core idea:** Python is the **permanent boss**. It never dies. C/Java/JS are temporary workers.

```
poly.py  →  parser.py  →  interpreter.py  →  Bridge
```

- `parser.py` splits your `.poly` file into `BlockNode` objects
- `interpreter.py` loops over each block, picks the right runner
- `Bridge` coordinates all shared state (variables + functions + objects)
- Python stays alive the **entire time** managing everything

**Key point:** When you run `poly script.poly`, ONE Python process starts and lives until the very end. Every other language is a child born and killed by Python.

---

## 🏛️ Pillar 2: The Template Engine (Variable Sharing)

**Core idea:** C/Java/JS run in separate processes — they can't see Python's memory. So the framework **bakes variables directly into the source code** before compiling.

**Flow:**
```
Bridge holds:  x=42, name="Alice"
       ↓
adapters.py → inject_globals() converts them per language
       ↓
runner.py assembles the full program:

   [injected globals]  +  [template bridge.h]  +  [your code]
           ↓
   subprocess.run(["gcc", "main.c", "-o", "main.exe"])
```

**Why injection styles differ:**

| Language | Generated Code | Reason |
|---|---|---|
| C/C++ | `static const long long x = 42;` | Compiler must know type before running |
| Java | `static final long x = 42L;` | Same — javac needs type declarations |
| JS | `globalThis["x"] = 42;` | No compiler — dynamically typed, assign at runtime |

**Templates** (`c_bridge.h`, `java_bridge.java`, `js_bridge.js`) are pre-written helper files that get pasted into every generated program to provide `export_value()` and `call_bridge()` functions.

---

## 🏛️ Pillar 3: The Interactive Pipe Protocol (Live Calling)

**Core idea:** C/Java/JS run as **subprocesses**. The framework connects Python ↔ subprocess using **stdin/stdout pipes as a walkie-talkie**.

**Subprocess creation in `runner.py`:**
```python
proc = subprocess.Popen(
    ["./main.exe"],
    stdin=subprocess.PIPE,   # Python writes answers here
    stdout=subprocess.PIPE,  # Python reads questions from here
)
```

**What freezes C — `fgets` in `c_bridge.h`:**
```c
static void _poly_call_raw(const char *name, const char *args_json) {
    printf("__POLY_CALL__|%s|%s\n", name, args_json);  // shout to Python
    fflush(stdout);                                      // send immediately
    fgets(__poly_ret_buf, sizeof(__poly_ret_buf), stdin); // ← FREEZE
}                                                        // blocking read — waits until Python replies
```

**The live conversation:**
```
C:      printf("__POLY_CALL__|add|[5,3]")   →→→ stdout pipe →→→ Python reads
C:      fgets(stdin)  ← FROZEN

Python: sees "__POLY_CALL__" → Dispatcher.call("add", 5, 3) → returns 8
Python: writes "__POLY_RET__|int|8"          ←←← stdin pipe ←←← to C

C:      fgets() returns, buffer = "__POLY_RET__|int|8"
C:      _parse_ret_i() extracts 8  ← UNFROZEN, continues
```

**Magic strings — why they exist:**  
C prints normal output too (like `printf("hello")`). Python uses string prefixes to tell apart bridge commands from regular output:

| String | Meaning |
|---|---|
| `__POLY_CALL__\|fn\|[args]` | Subprocess asking Python to call a function |
| `__POLY_RET__\|type\|val` | Python sending back a return value |
| `__POLY_EXPORT__\|name\|type\|val` | Subprocess exporting a variable to the bridge |
| `__POLY_REGISTER__\|...` | Subprocess registering a function stub |
| anything else | Normal print → show on terminal |

**`protocol.py` reading loop** handles all of this — it's the Python side that reads every line the subprocess prints and decides what to do.

---

## 🏛️ Pillar 4: Recursive Vice-Versa Routing

**Core idea:** What if Java wants to call a **JavaScript** function? Neither is Python. The Dispatcher solves this using **stub_runner**.

**How a JS function gets registered:**
```
JS block prints:  __POLY_REGISTER__|multiply|js|int|"function(x){return x*10;}"
                          ↓
protocol.py reads it → stores in FunctionRegistry:
  functions["multiply"] = FunctionEntry(
      language = "js",
      stub_source = "function(x){ return x*10; }",
      func = None   ← no Python callable!
  )
```

**Now Java calls it — Dispatcher's two-path decision:**
```
Java prints:  __POLY_CALL__|multiply|[5]
                    ↓
Dispatcher.call("multiply", 5)
                    ↓
  entry.func = None?         YES → skip direct call
  entry.stub_source exists?  YES → send to stub_runner
                    ↓
stub_runner.invoke("multiply", "js", source, args=[5])
                    ↓
  builds complete runnable JS:
    function __stub_fn(x){ return x*10; }
    var r = __stub_fn.apply(null, [5]);
    process.stdout.write("__POLY_RET__|int|" + r)
                    ↓
  subprocess.Popen(["node", "-e", snippet])
  reads back: "__POLY_RET__|int|50"
                    ↓
Dispatcher returns 50 to Java
```

**Full routing chain:**
```
Java → Python (protocol.py) → Dispatcher → stub_runner → Node.js subprocess → 50 → Java
```

---

## 🏛️ Pillar 5: Global OOP — Object Handles

**Core idea:** A Python object cannot physically exist inside Java's JVM or C's memory. So Python keeps the real object and gives other languages a **numbered ticket (handle)**.

**Python stores the object:**
```python
counter = Counter()           # real Python object
handle = store_object(counter) # ObjectStore assigns handle = 1
export("h", handle)           # bridge stores: h = 1
```

**Java gets a plain integer:**
```java
static final long h = 1L;   // just a number, not the real object
```

**Java calls a method using the handle:**
```
Java prints:  __POLY_METHOD__|1|increment|[]
                    ↓
protocol.py reads it → context.call_method(handle=1, method="increment")
                    ↓
ObjectStore.get(1) → retrieves the real Python Counter object
                    ↓
getattr(counter, "increment")()   ← real method called in Python memory
                    ↓
result sent back to Java via stdin pipe
```

**ObjectStore is just a dictionary:**
```python
_objects = {
    1: <Counter instance>,
    2: <User instance>,
    3: [10, 20, 30]
}
# C/Java/JS only ever hold the numbers 1, 2, 3
```

---

## 🔗 All 5 Pillars Together — One Example

```
global { x = 100 }             ← Pillar 1: interpreter reads this block

python {
    def add(a,b): return a+b
    export_function("add", add) ← Pillar 1: registered in FunctionRegistry
}

c {
    // x was injected as:          Pillar 2: Template Engine
    // static const long long x = 100;

    long long r = call_bridge("add", x, 50);
    //              ↑
    //   printf("__POLY_CALL__|add|[100,50]")   Pillar 3: Pipe Protocol
    //   fgets(stdin)  ← FROZEN
    //
    //   Python: Dispatcher.call("add", 100, 50)
    //     → entry.func exists → calls directly → 150
    //   Python: writes "__POLY_RET__|int|150"
    //   C unfreezes, r = 150
}

java {
    export_bridge_function("square","long square(long x){return x*x;}","int");
    // → __POLY_REGISTER__ stored in FunctionRegistry as stub
}

python {
    result = call("square", 12)
    // Dispatcher: entry.func=None, stub_source exists
    //   → stub_runner compiles Java square()   Pillar 4: Vice-Versa Routing
    //   → returns 144
}

python {
    mylist = [1,2,3]
    h = store_object(mylist)     ← Pillar 5: Object Handles
    export("list_handle", h)     → h = 1 sent to Java as integer
}
// Java calls __POLY_METHOD__|1|append|[4]
// Python: ObjectStore.get(1) → mylist.append(4)
```

---

## Summary Table

| Pillar | Problem Solved | Key Mechanism | Key Files |
|---|---|---|---|
| **1** | Who coordinates everything? | Python master process, Bridge | `interpreter.py`, `bridge.py`, `dispatcher.py` |
| **2** | How do variables reach C/Java/JS? | Inject into source before compile | `adapters.py`, `runner.py`, `templates/` |
| **3** | How does C call Python mid-execution? | `printf` + `fgets(stdin)` pipe freeze | `c_bridge.h`, `protocol.py` |
| **4** | How does Java call JS (non-Python)? | Dispatcher → stub_runner → micro subprocess | `dispatcher.py`, `stub_runner.py` |
| **5** | How do objects cross language boundaries? | Numeric handles, ObjectStore | `object_store.py`, `protocol.py`, `context.py` |

### User Input

tell me the reverse way of pillar 3

### Planner Response

## Reverse of Pillar 3 — Python Calling C

---

## Pillar 3 Direction (What You Already Know)

```
C wants something from Python

C  ──── __POLY_CALL__ ────→  Python
C  ←─── __POLY_RET__  ────  Python
```
C is the **asker**. Python is the **answerer**. C freezes with `fgets`.

---

## Reverse Direction — Python Calling C

```
Python wants something from C

Python  ──→  stub_runner  ──→  spawn C subprocess  ──→  C runs
Python  ←──────────────────────────────────────────── C prints __POLY_RET__
```
Now **Python is the asker**. C is the **answerer**. Python waits for the subprocess to finish.

---

## Step By Step

### Step 1 — C registers a function

```c
// In your .poly C block:
export_bridge_function("square", "int square(int x){ return x*x; }", "int");
```

This prints to stdout:
```
__POLY_REGISTER__|square|c|int|"int square(int x){ return x*x; }"
```

Python reads it → stores in `FunctionRegistry`:
```python
functions["square"] = FunctionEntry(
    language    = "c",
    stub_source = "int square(int x){ return x*x; }",
    func        = None   # ← no Python callable
)
```

---

### Step 2 — Python calls it

```python
# In your .poly Python block:
result = call("square", 7)
```

---

### Step 3 — Dispatcher decides

```python
# dispatcher.py
entry = registry.get_function("square")

entry.func        = None   # ← not a Python function
entry.stub_source = "..."  # ← C source code exists

# → sends to stub_runner
stub_runner.invoke("square", "c", source, return_type="int", args=[7])
```

---

### Step 4 — stub_runner builds a complete C program

```python
# stub_runner.py — _run_c_stub()

source = "int square(int x){ return x*x; }"
args_c = "7LL"

snippet = """
int square(int x){ return x*x; }
int main(void) {
    printf("__POLY_RET__|int|%lld\n", (long long)(square(7LL)));
    return 0;
}
"""
```

It wraps your C function in a `main()` that **automatically calls it and prints the result**.

---

### Step 5 — Python spawns C as a subprocess

```python
# runner.py
subprocess.run(["gcc", "main.c", "-o", "main.exe"])  # compile

# protocol.py - run_subprocess()
proc = subprocess.Popen(["./main.exe"], stdout=PIPE)
```

C runs, prints:
```
__POLY_RET__|int|49
```

Python reads it → `decode_return("__POLY_RET__|int|49")` → returns `49`

---

### Step 6 — Python gets the answer

```python
result = call("square", 7)
print(result)   # 49
```

---

## Side-by-Side Comparison

| | Pillar 3 (C → Python) | Reverse (Python → C) |
|---|---|---|
| **Who asks** | C subprocess | Python main process |
| **Who answers** | Python | C subprocess |
| **How C asks** | `printf("__POLY_CALL__...")` then `fgets` freeze | — |
| **How Python asks** | — | `stub_runner` builds + compiles + runs a fresh C process |
| **How answer comes back** | Python writes to C's `stdin` | C prints `__POLY_RET__` to stdout, Python reads |
| **What freezes** | C freezes with `fgets(stdin)` | Python waits for subprocess to finish |
| **Key file** | `c_bridge.h` + `protocol.py` | `stub_runner.py` + `runner.py` |

---

## The Key Difference

In Pillar 3 — C is a **long-running subprocess** that pauses and resumes multiple times using `fgets`.

In the Reverse — Python creates a **brand new fresh C subprocess** just for that one function call. It runs, prints the answer, and immediately dies.

```
Pillar 3:    [C subprocess lives]──pause──resume──pause──resume──[dies]
                                      ↕         ↕
                                    Python    Python

Reverse:     Python → [new C subprocess born] → prints result → [immediately dies]
```

### User Input

there is no freze in python?

### Planner Response

## Yes! Python Also Freezes — But Differently

---

## How Python Freezes

When Python calls a C stub, it freezes in **two places** inside `protocol.py`:

### Freeze 1 — During Compilation
```python
# runner.py
cp = subprocess.run(["gcc", "main.c", "-o", "main.exe"])
#                   ↑
# subprocess.run() BLOCKS Python until gcc finishes compiling
# Python cannot move forward until main.exe is ready
```

### Freeze 2 — During Execution
```python
# protocol.py — run_subprocess()
for raw in proc.stdout:    # ← Python BLOCKS here
    line = raw.strip()
    # reads line by line...
    # Python is STUCK in this loop until
    # the C subprocess closes and stdout ends
```

---

## So Both Freeze — But Different Mechanisms

| | C Freezes (Pillar 3) | Python Freezes (Reverse) |
|---|---|---|
| **How** | `fgets(stdin)` — waits for one specific reply line | `for raw in proc.stdout` — waits until entire subprocess finishes |
| **When it unfreezes** | The moment Python writes one `__POLY_RET__` line | The moment the C process exits completely |
| **Can it resume mid-way?** | ✅ YES — C can freeze and unfreeze multiple times | ❌ NO — Python reads until C is fully done |
| **Called** | Blocking read on stdin | Blocking iteration on stdout |

---

## Visual Comparison

```
C freezes (Pillar 3) — multiple pause/resume cycles:

C:    run → pause → resume → pause → resume → done
              ↕               ↕
           Python          Python
           answers         answers


Python freezes (Reverse) — one long wait:

Python:  call stub_runner → FROZEN (waiting) → gets result
                                ↕
                    C: runs completely, prints result, exits
                    Python unfreeze only after C fully exits
```

---

## Why C's Freeze Feels More "Active"

- **C's `fgets`** — C is mid-execution, pauses for ONE answer, then keeps running more code. It can ask Python **multiple times**.
- **Python's `for raw in proc.stdout`** — Python just waits passively for the whole C program to finish. C doesn't get to "ask back."

---

## One-Line Summary

> **Both freeze** — C uses `fgets(stdin)` to pause mid-run waiting for one reply. Python uses `for raw in proc.stdout` to wait until the entire subprocess is done. C's freeze is **interactive**. Python's freeze is **passive waiting**.

### User Input

explai dispatcher in pillar 3  and then complete flow

### Planner Response

## Dispatcher in Pillar 3 + Complete Flow

---

## Where Dispatcher Sits in Pillar 3

```
C prints __POLY_CALL__
        ↓
protocol.py reads it
        ↓
context.call(fn_name, *args)
        ↓
bridge.call()
        ↓
Dispatcher.call()    ← HERE
        ↓
finds entry.func → calls Python function directly
        ↓
result goes back to protocol.py
        ↓
protocol.py writes __POLY_RET__ to C's stdin
        ↓
C unfreezes
```

---

## Dispatcher's Exact Job in Pillar 3

In Pillar 3, C is calling a **Python function** that was registered earlier. So when Dispatcher checks:

```python
def call(self, name, *args, context=None):
    entry = self._registry.get_function(name)

    if entry.func is not None:        # ← THIS path is taken in Pillar 3
        return entry.func(*args)      # Python function called directly
                                      # No subprocess, no compiling

    if entry.stub_source is not None: # ← This is Pillar 4 (non-Python stubs)
        return stub_runner.invoke(...)
```

In Pillar 3 — `entry.func` **always exists** because the function was registered by Python's `export_function()`. So Dispatcher just **calls it directly** and returns the result immediately.

---

## Complete Flow — Every Single Step

### Setup: The `.poly` file

```
python {
    def add(a, b):
        return a + b
    export_function("add", add)
}

c {
    long long result = call_bridge_i("add", "[5, 3]");
    printf("Result = %lld\n", result);
}
```

---

### Phase 1 — Python Block Runs

```
interpreter.py sees lang = "python"
        ↓
python_lang.py runs the block using exec()
        ↓
export_function("add", add) is called
        ↓
context.export_function("add", add)
        ↓
bridge.register_python_function("add", add)
        ↓
FunctionRegistry stores:
    functions["add"] = FunctionEntry(
        name     = "add",
        language = "python",
        func     = <add function>,   ← real Python callable
        stub_source = None
    )
```

---

### Phase 2 — C Block Starts (Compilation)

```
interpreter.py sees lang = "c"
        ↓
languages/__init__.py → _make_run("c") → runner.run("c", code, context)
        ↓
runner.py:

  1. adapters.py inject_globals(context)
     generates:  (no globals to inject in this example)

  2. opens c_bridge.h template → reads all macros

  3. assembles full source:
     ┌──────────────────────────────────────┐
     │ #include <stdio.h>                   │
     │ ...c_bridge.h macros...              │  ← bridge glue
     │ static void _poly_call_raw(...) {    │
     │     printf("__POLY_CALL__|...")      │
     │     fflush(stdout)                   │
     │     fgets(..., stdin)   ← freeze!    │
     │ }                                    │
     │                                      │
     │ long long result =                   │  ← your C code
     │   call_bridge_i("add", "[5,3]");    │
     │ printf("Result = %lld\n", result);   │
     └──────────────────────────────────────┘

  4. writes to temp file: C:\Temp\plf_c_abc\main.c

  5. subprocess.run(["gcc", "main.c", "-o", "main.exe"])
     Python FREEZES here until gcc finishes
     gcc exits → main.exe is ready
```

---

### Phase 3 — C Subprocess Starts

```
runner.py calls run_subprocess(["./main.exe"], context, parse_export)
        ↓
protocol.py — run_subprocess():

  proc = subprocess.Popen(
      ["./main.exe"],
      stdin  = PIPE,
      stdout = PIPE,
      stderr = PIPE
  )

  Python enters the reading loop:
  for raw in proc.stdout:   ← Python now reads every line C prints
      ...
```

C process starts running its `main()`:

```c
long long result = call_bridge_i("add", "[5, 3]");
// call_bridge_i calls _poly_call_raw("add", "[5,3]")
```

---

### Phase 4 — C Freezes, Python Wakes Up

```
C:
  printf("__POLY_CALL__|add|[5,3]\n")  → stdout pipe → Python reads
  fflush(stdout)                        → forces immediate delivery
  fgets(__poly_ret_buf, ..., stdin)     → FROZEN — waiting for reply
```

Python's reading loop in `protocol.py` receives the line:

```python
for raw in proc.stdout:
    line = raw.strip()
    # line = "__POLY_CALL__|add|[5,3]"

    if line.startswith("__POLY_CALL__|"):
        payload    = line[len("__POLY_CALL__|"):]  # "add|[5,3]"
        sep        = payload.find("|")
        fn_name    = payload[:sep]                 # "add"
        args_json  = payload[sep+1:]               # "[5,3]"
        args       = json.loads(args_json)         # [5, 3]
```

---

### Phase 5 — Dispatcher Called

```python
result = context.call(fn_name, *args)
# context.call("add", 5, 3)
        ↓
bridge.call("add", 5, 3, context=self)
        ↓
Dispatcher.call("add", 5, 3)
        ↓
entry = registry.get_function("add")
# entry.func = <add function>  ← exists!
# entry.stub_source = None

entry.func(5, 3)   ← calls Python's add(5, 3) directly
# returns 8
```

---

### Phase 6 — Python Sends Result Back to C

```python
# back in protocol.py
_send(result)    # result = 8

def _send(value):
    proc.stdin.write(encode_return(value))
    proc.stdin.flush()

# encode_return(8):
# returns "__POLY_RET__|int|8\n"

# Python writes:  "__POLY_RET__|int|8\n"  →  C's stdin pipe
```

---

### Phase 7 — C Unfreezes, Reads Result

```c
// fgets() returns because Python wrote a line
// __poly_ret_buf = "__POLY_RET__|int|8\n"

// _parse_ret_i() searches for "|int|" in buffer:
// finds "8" → returns 8LL

long long result = 8;   // call_bridge_i() returned 8
printf("Result = %lld\n", result);
// prints:  Result = 8
```

---

### Phase 8 — C Exits, Python Reads Export, Cleanup

```
C finishes → process exits
        ↓
protocol.py's for loop ends (stdout closed)
        ↓
run_subprocess returns: ({}, None)
  ← no exports, no stub_return in this example
        ↓
runner.py: shutil.rmtree(build_dir)
  ← deletes temp folder, main.c and main.exe gone
        ↓
interpreter.py moves to next block (if any)
```

---

## Complete Flow — One Diagram

```
poly.py
  └── parser.py → [BlockNode("python",...), BlockNode("c",...)]
        └── interpreter.py loops:

BLOCK 1 - python:
  python_lang.py exec()
    export_function("add", add)
      → FunctionRegistry["add"] = FunctionEntry(func=<add>)

BLOCK 2 - c:
  runner.py
    ├── inject_globals()        → no globals here
    ├── read c_bridge.h         → get macros
    ├── assemble full source    → main.c
    ├── subprocess.run(gcc)     → Python FREEZES (compile)
    │                           → Python UNFREEZES (main.exe ready)
    └── run_subprocess(main.exe)
          │
          ├── Popen(stdin=PIPE, stdout=PIPE)
          │
          └── for raw in proc.stdout:  ← Python reading loop
                │
                C runs: call_bridge_i("add", "[5,3]")
                  │
                  C: printf("__POLY_CALL__|add|[5,3]")
                  C: fgets(stdin)  ← C FROZEN
                │
                Python reads "__POLY_CALL__|add|[5,3]"
                  │
                  context.call("add", 5, 3)
                    └── bridge.call()
                          └── Dispatcher.call()
                                └── entry.func(5,3) → 8
                  │
                  proc.stdin.write("__POLY_RET__|int|8")
                │
                C: fgets returns  ← C UNFROZEN
                C: result = 8
                C: printf("Result = 8")
                │
                Python reads "Result = 8"
                  └── no magic prefix → just print to terminal
                │
                C exits
                for loop ends

  shutil.rmtree(temp folder)  ← cleanup
```

---

## Dispatcher's Role — One Line

> In Pillar 3, Dispatcher's only job is: **look up the function name → find the Python callable → call it → return the result** back to `protocol.py` which sends it to the frozen C process.

### User Input

explain pillar 5 clearly

### Planner Response

Let me read the actual object store and protocol code again to give you the most accurate explanation.

*Viewed [14_object_handles.poly](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/example/14_object_handles.poly) *

*Viewed [18_method_proxy_bridge.poly](file:///c:/Users/G%20SIREESH%20REDDY/OneDrive/Desktop/Phase_2_PLF/PNI/example/18_method_proxy_bridge.poly) *

### Planner Response

Now I have everything. Here's the clearest explanation of Pillar 5:

---

## 🏛️ Pillar 5: Global OOP — Object Handles Explained Clearly

---

## The Core Problem

A Python object like `Counter(10)` lives **inside Python's memory**. It has methods like `.increment()` and `.get_value()`.

Now imagine Java wants to call `counter.increment(5)`.

**The problem:**
```
Python memory:   [Counter object at 0x7f3a...]   ← real object lives here
Java's JVM:      ???                              ← completely separate world
C process:       ???                              ← completely separate world
```

Java's JVM and C **cannot reach into Python's memory**. They are different processes. There is no shared RAM.

---

## The Solution: A Ticket Number (Handle)

Instead of sending the real object (impossible), Python gives other languages a **simple integer — the handle**. Like a coat check ticket.

```
Python stores object → gets ticket #1
Python tells Java: "the counter is at ticket #1"
Java holds: handle = 1   (just a number)

Java wants to call increment():
  Java says: "run increment() on ticket #1"
  Python: looks up ticket #1 → finds the real Counter → calls increment()
  Python: sends result back to Java
```

The real object **never leaves Python**. Only the number travels.

---

## Step-by-Step Using the Real Example (`18_method_proxy_bridge.poly`)

### Step 1 — Python Creates and Stores the Object

```python
# Python block:
class Counter:
    def __init__(self, initial):
        self.value = initial
    def increment(self, amount):
        self.value += amount
        return self.value

my_counter = Counter(10)           # create object, value=10
handle_id  = store_object(my_counter)  # store it, get ticket
export("bridge_counter_handle", handle_id)  # share the ticket number
```

**Inside `ObjectStore`:**
```python
def put(self, obj) -> int:
    handle = self._next_id      # handle = 1
    self._objects[1] = my_counter  # store the real object
    self._next_id += 1          # next handle will be 2
    return 1                    # give ticket #1 back
```

**ObjectStore is now:**
```
_objects = {
    1: <Counter instance, value=10>
}
```

**Bridge now has:**
```
bridge_counter_handle = 1    ← just an integer in shared memory
```

---

### Step 2 — C Gets the Handle as a Plain Integer

Pillar 2 (Template Engine) injects globals into C source:

```c
// Generated by inject_c_globals():
static const long long bridge_counter_handle = 1;
//                                             ↑
//                              just a number, not the object
```

C doesn't know what a `Counter` is. It just sees the number `1`.

---

### Step 3 — C Calls a Method Using the Handle

```c
// C block:
long long hnd = bridge_counter_handle;    // hnd = 1
long long res = call_method_i(hnd, "increment", "[10]");
//              ↑
//  This is from c_bridge.h template
```

**What `call_method_i` does in `c_bridge.h`:**

```c
static void _poly_method_raw(long long handle, const char *method, const char *args_json) {
    printf("__POLY_METHOD__|%lld|%s|%s\n", handle, method, args_json);
    // prints:  __POLY_METHOD__|1|increment|[10]
    fflush(stdout);
    fgets(__poly_ret_buf, sizeof(__poly_ret_buf), stdin);  // FREEZE — wait
}
```

C prints the magic string and **freezes** with `fgets` — exactly like Pillar 3.

---

### Step 4 — Python Reads `__POLY_METHOD__`

In `protocol.py` reading loop:

```python
elif line.startswith(METHOD_MARKER):
    # line = "__POLY_METHOD__|1|increment|[10]"
    parts = line[len(METHOD_MARKER):].split("|", 2)
    # parts = ["1", "increment", "[10]"]

    handle = int(parts[0])      # 1
    method = parts[1]           # "increment"
    m_args = json.loads(parts[2]) # [10]

    result = context.call_method(handle, method, *m_args)
    #                ↑ goes to bridge → ObjectStore
    _send(result)   # send __POLY_RET__|int|21 back to C
```

---

### Step 5 — ObjectStore Fetches the Real Object

```python
# context.call_method(1, "increment", 10)
#   → bridge.call_method(1, "increment", 10)

def call_method(self, handle, method, *args):
    obj = self.load_object(handle)        # ObjectStore.get(1)
    #                                     # → returns the real Counter object
    return getattr(obj, method)(*args)    # Counter.increment(10)
    #                                     # value was 10, now 20, returns 20
```

**ObjectStore lookup:**
```python
def get(self, handle):
    return self._objects.get(handle)
# _objects[1] = <Counter, value=10>
# returns the real Counter object
```

**Python calls the method:**
```python
getattr(counter, "increment")(10)
# counter.value = 10 + 10 = 20
# returns 20
```

---

### Step 6 — Result Goes Back to C

```python
_send(20)
# proc.stdin.write("__POLY_RET__|int|20\n")
```

C unfreezes:
```c
// fgets got:  "__POLY_RET__|int|20"
long long res = call_method_i(hnd, "increment", "[10]");
// res = 20
printf("[C] Result: %lld\n", res);  // prints: [C] Result: 20
```

---

### Step 7 — Python Block 2 Verifies

```python
# Second Python block:
handle    = get_global("bridge_counter_handle")   # gets 1
recovered = load_object(handle)                   # ObjectStore.get(1)
print(recovered.get_value())                      # Counter.value = 20 ✅

delete_object(handle)   # ObjectStore removes key 1 → garbage collected
```

---

## Complete Picture

```
Python Memory (ObjectStore):
┌─────────────────────────────────┐
│  handle 1  →  Counter(value=10) │  ← real object, never leaves Python
└─────────────────────────────────┘
       ↑ only Python can touch this

Bridge Shared Memory:
┌──────────────────────────────────┐
│  bridge_counter_handle  =  1     │  ← just a number, everyone can see
└──────────────────────────────────┘
                │
    ┌───────────┼───────────┐
    ↓           ↓           ↓
   C gets      Java gets   JS gets
  long long=1  long=1      number=1

C wants increment(10):
  prints: __POLY_METHOD__|1|increment|[10]
  FREEZES with fgets(stdin)

Python reads it:
  ObjectStore.get(1) → Counter object
  Counter.increment(10) → value: 10+10 = 20
  writes: __POLY_RET__|int|20

C UNFREEZES: res = 20
```

---

## Why This Design?

| Option | Problem |
|---|---|
| Send the whole object to C | Impossible — C doesn't understand Python objects |
| Recreate the object in C | C has no classes, no methods, no Python GC |
| Use a handle number ✅ | Works — a number crosses any language boundary. Object stays safe in Python |

---

## Three Key Functions in `context.py`

```python
store_object(obj)       → saves obj in ObjectStore, returns handle (int)
load_object(handle)     → retrieves real object by handle
delete_object(handle)   → removes from ObjectStore (frees memory)
call_method(handle, method, *args) → load object + call method on it
```

---

## One-Line Summary

> Python keeps the real object in `ObjectStore`. Other languages hold only a **ticket number (handle)**. When they want to call a method, they send `__POLY_METHOD__|handle|method|args` — Python looks up the ticket, calls the real method, sends result back.

### User Input

is there any reverse for this

### Planner Response

## Is There a Reverse for Pillar 5?

**Short answer: No. And here's exactly why.**

---

## What Pillar 5 Does (Forward)

```
Python creates object → stores in ObjectStore → gives handle to C/Java/JS
C/Java/JS holds handle → calls method → Python executes it → result back
```

The object **lives in Python** because Python is the **permanent process**.

---

## Why Reverse Is Impossible

The reverse would be:
```
C creates a struct → gives handle to Python
Python calls methods on C struct
```

**But this can't work for one fundamental reason:**

```
Block 1 - C runs:
  Counter c = {10};   ← C struct created in C process memory
  // C process DIES after this block
  // That struct is GONE from RAM

Block 2 - Python runs:
  load_object(1)   ← what object? The C process is dead!
```

C/Java/JS are **subprocesses that are born and die per block**. When the block ends, the process exits and **all its memory is wiped**. There is nothing left to hold a handle to.

---

## Python vs C/Java/JS Lifetime

```
Timeline:

Python process: |════════════════════════════════════| (lives forever)

C block:        |═════|                               (born, dies)
Java block:              |═════|                      (born, dies)
JS block:                        |═════|              (born, dies)
C block again:                            |═════|     (fresh process, born, dies)
```

Python's `ObjectStore` works because Python **never dies**. It holds the objects across all blocks. A C struct has no such permanent home.

---

## The Closest Thing to a Reverse

The closest reverse that **does exist** is from **Pillar 4** — C/Java/JS registering **functions** (not objects):

```
C registers a function:
  export_bridge_function("square", "int square(int x){return x*x;}", "int")

Python calls it:
  result = call("square", 7)   → stub_runner compiles fresh C → runs → 49
```

But this is **stateless** — every call compiles and runs a brand new process. There is no persistent C object with evolving state. You can't do:

```python
call("counter.increment")   # ❌ no persistent counter in C
call("counter.increment")   # ❌ second call has no memory of first
```

---

## Summary Table

| Direction | Possible? | How |
|---|---|---|
| Python object → C/Java/JS uses handle | ✅ YES | ObjectStore + `__POLY_METHOD__` |
| C/Java/JS object → Python uses handle | ❌ NO | C process dies after each block — nothing to hold |
| C/Java/JS registers **function** → Python calls it | ✅ YES (Pillar 4) | stub_runner — but stateless, no persistent object |

---

## One-Line Reason

> **Reverse is impossible because C/Java/JS die after every block. Python is the only permanent process, so it is the only one that can own and store objects long-term.**