# 🏛️ Polyglot Framework Architecture Reference

This document visualizes the complete inner workings of the Polyglot Framework. These architectural diagrams explain the exact data flow, memory mapping, and process management for every core feature.

---

## 1. Top-Level Process Architecture (The Bird's Eye View)

The framework runs as a single **Master Python Process** that launches and orchestrates multiple **Child Subprocesses** over standard IO.

```mermaid
flowchart TD
    subgraph Master_Process_Python
        CLI["poly.py"] --> Interpreter["core/interpreter.py"]
        Interpreter --> Bridge["bridge/poly_bridge.py"]
        
        Bridge --> Context[("Bridge Shared Context")]
        Bridge --> OR[("Object Registry")]
        Bridge --> Dispatch["Dispatcher"]
    end

    subgraph Subprocesses_Piped_Execution
        Dispatch -->|"spawn & pipe"| C_Lang["C Executable"]
        Dispatch -->|"spawn & pipe"| Node["JavaScript V8"]
        Dispatch -->|"spawn & pipe"| Java["JVM"]
    end

    Context -.->|"JSON Inject"| Node
    Context -.->|"String Inject"| C_Lang
```

---

## 2. Feature: Unidirectional Memory Sharing (Phase 2 Variable Injection)

How do primitive variables (like `x = 10`) move from Python into C or JavaScript? They do not share RAM. The bridge *generates source code* on the fly.

```mermaid
sequenceDiagram
    participant User
    participant Core
    participant Mem
    participant C_Compiler

    User->>Core: global { x = 10 }
    Core->>Mem: Store {x: 10}
    
    User->>Core: c { print x }
    Core->>Mem: Fetch {x: 10}
    
    Note right of C_Compiler: Bridge dynamically prepends C-Macro before compiling
    
    Core->>C_Compiler: Compile source code
    C_Compiler->>User: stdout: 10
```

---

## 3. Feature: The Interactive Pipe Protocol (Live Function Calling)

This is the cornerstone of Phase 3. It allows languages to interact *after* they have been compiled and are actively running.

```mermaid
flowchart LR
    subgraph Compiled_Subprocess
        App["C++ Code"] -->|"call_bridge"| SysOut["stdout buffer"]
        SysIn["stdin buffer"] -->|"read"| App
    end

    SysOut -->|"POLY_CALL"| PipeRunner["bridge/pipe_runner.py"]

    subgraph Host_Master_Process
        PipeRunner -->|"parse"| Dispatcher
        Dispatcher -->|"execute"| PyFunc["Python Memory"]
        PyFunc -->|"return value"| PipeRunner
    end

    PipeRunner -->|"POLY_RET"| SysIn
```

---

## 4. Feature: Recursive Stub Architecture (Vice-Versa Function Routing)

When JavaScript wants to call a block of C code, the Python bridge acts as the middleman (router). It dynamically spins up a one-shot worker of the target language.

```mermaid
sequenceDiagram
    participant JS_Engine
    participant Python_Hub
    participant C_Worker

    JS_Engine->>Python_Hub: POLY_CALL c_multiplier
    Note over JS_Engine: Suspends execution
    
    Python_Hub->>C_Worker: Spawns c_worker
    Note over Python_Hub: Passes array to C
    
    C_Worker->>Python_Hub: POLY_RET int 50
    Note over C_Worker: Worker Terminates
    
    Python_Hub->>JS_Engine: POLY_RET int 50
    Note over JS_Engine: Resumes execution with 50
```

---

## 5. Feature: Global OOP & Methods (Phase 3E Object Proxies)

How do you pass a customized Python `class` to Java and let Java invoke its methods natively? 
Using **Integer Handle IDs** mapped to auto-generated Proxy Code.

```mermaid
flowchart TD
    subgraph Python_Master
        PyObj["Python Counter Instance"]
        Store[("Object Store")]
        PyObj <-->|"Assigned Handle ID 4"| Store
    end

    Store -->|"Exports Schema & Handle ID"| Java_Compiler

    subgraph Java_Process
        Java_Compiler -->|"Generates Native Class"| Proxy["Java Counter Proxy"]
        Proxy -->|"Holds local variable handle 4"| Logic
        
        Logic["Java App calls: counter.increment()"] -->|"Routes request"| MethodPipe
        MethodPipe["Emit: POLY_METHOD 4 increment"]
    end

    MethodPipe -->|"Intercepted by Python"| Store
    Store -->|"Triggers PyObj.increment()"| PyObj
```

---

## 6. Feature: Class Schema Code-Generation

Before the object handle is passed, the target language must perfectly replicate the class blueprint so it knows what methods exist. PolyBridge acts as a transpiler for schemas.

```mermaid
flowchart LR
    PySchema["Python export schema"] --> Registry[("Schema Registry")]
    
    Registry --> C_Adapter["cpp_lang.py"]
    C_Adapter -->|"Generates"| C_Code["C++ struct Point"]
    
    Registry --> Java_Adapter["java_lang.py"]
    Java_Adapter -->|"Generates"| Java_Code["Java class Point"]
```
