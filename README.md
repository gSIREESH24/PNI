# Polyglot Runtime

A system that runs code in multiple languages (Python, JavaScript, C, Java, and C++) in a single `.poly` file.

---

## Table of Contents
1. [Overview](#overview)
2. [Step-by-Step Flow](#step-by-step-flow)
3. [Project Structure](#project-structure)
4. [Usage](#usage)

---

## Overview

The Polyglot Runtime allows you to write a single `.poly` file containing code blocks in different programming languages (Python, JavaScript, C, Java, and C++). The runtime:
- **Parses** the `.poly` file to extract language-specific code blocks
- **Shares variables** across languages using a global context
- **Executes** each block with the appropriate language runtime
- **Manages** compilation and execution for compiled languages like C, C++, and Java

---

## Step-by-Step Flow

### **Step 1: Entry Point (`poly.py`)**
```
User runs: python poly.py script.poly
    ↓
- Reads the .poly file containing mixed language code
- Calls parse() to break it into language blocks
- Calls interpret() to execute each block
```

### **Step 2: Parsing (`core/parser.py`)**
The parser identifies and extracts language blocks from the source code:

```
Source Code Example:
    global { x = 10 }
    python { print(x) }
    javascript { console.log(x) }
    
Parser Process:
    ↓
1. Looks for language name followed by opening brace "{"
2. Collects all code until matching closing brace "}"
3. Creates BlockNode objects for each block
    ↓
Output: ProgramNode containing:
    [
        BlockNode("global", "x = 10"),
        BlockNode("python", "print(x)"),
        BlockNode("javascript", "console.log(x)")
    ]
```

**How it works:**
- Reads source code line by line
- Detects `language {` as block start
- Tracks brace depth `{` and `}` to find block end
- Cleans up indentation using `textwrap.dedent()`
- Stores each block as a `BlockNode` with language and code

---

### **Step 3: Interpretation (`core/interpreter.py`)**
The interpreter processes each block sequentially and manages execution:

```
For each BlockNode in the program:

1. If language = "global":
   ↓
   process_global() function:
   - Parses variable assignments like "x = 10"
   - Stores variables in Context (shared memory)

2. If language = "python" or "javascript" or "js" or "c" or "c++" or "cpp" or "java":
   ↓
   - Retrieves language runner from LANGUAGE_REGISTRY
   - Passes context and code to the runner
   - Executes with appropriate runtime
   - Context is updated with new variables created
```

**Context Object (`core/context.py`):**
- Acts as a **shared dictionary** across all language blocks
- `set(key, value)` - Store a variable
- `get(key)` - Retrieve a variable
- `all()` - Get all variables

---

### **Step 4: Language Runners (`languages/` folder)**

Each language has its own runner that handles execution:

#### **Python Runner** (`languages/python_lang.py`):
```python
run(code, context):
    1. Creates export() function to share variables
    2. Copies all context.variables into local environment
    3. Executes the Python code using exec()
    4. Updates context with new variables created in code
```

**Example:**
```
Global: { x = 10 }
    → Context stores: {x: 10}

Python: { y = x + 5; export('result', y) }
    → Injects: x = 10 into Python environment
    → Executes: y = x + 5
    → Updates Context: {x: 10, result: 5}
```

#### **JavaScript Runner** (`languages/js_lang.py`):
```python
run(code, context):
    1. Converts context variables to JSON
    2. Injects them as JavaScript: var x = 10;
    3. Prepends variables to user code
    4. Executes via Node.js: node -e "var x = 10; [code]"
```

**Example:**
```
Global: { x = 5 }

JavaScript: { console.log(x) }
    → Generates: var x = 10;
                 console.log(x);
    → Runs with Node.js
    → Output: 10
```

#### **C Runner** (`languages/c_lang.py`):
```python
run(code):
    1. Creates temporary .c file with user code
    2. Compiles with gcc: gcc file.c -o file.exe
    3. Executes: file.exe
    4. Cleans up temporary files
```

**Note:** C does not receive context (no variable sharing to C)

#### **C++ Runner** (`languages/cpp_lang.py`):
```python
run(code):
    1. Creates temporary .cpp file with user code
    2. Compiles with g++: g++ file.cpp -o file.exe
    3. Executes: file.exe
    4. Cleans up temporary files
```

**Note:** C++ does not receive context (no variable sharing to C++)

#### **Java Runner** (`languages/java_lang.py`):
```python
run(code):
    1. Creates a temporary Java source file
    2. Detects the class name, or wraps plain statements in a Main class
    3. Compiles with javac
    4. Executes with java -cp
```

**Note:** Java does not receive context (no variable sharing to Java)

---

## Project Structure

```
poly_runtime/
│
├── poly.py                 # Main entry point
├── poly.bat               # Windows batch script to run poly
├── README.md              # This file
│
├── core/                  # Core interpreter logic
│   ├── ast.py            # Abstract Syntax Tree nodes
│   ├── context.py        # Shared variable storage
│   ├── executor.py       # (Legacy - see interpreter.py)
│   ├── interpreter.py    # Main interpreter loop
│   ├── lexer.py          # Tokenizer (simple line splitter)
│   └── parser.py         # Parser (extracts language blocks)
│
└── languages/            # Language-specific runners
    ├── __init__.py       # Language registry
    ├── python_lang.py    # Python execution
    ├── js_lang.py        # JavaScript/Node.js execution
    ├── c_lang.py         # C compilation and execution
    ├── cpp_lang.py       # C++ compilation and execution
    └── java_lang.py      # Java compilation and execution
```

---

## Usage

### Basic Syntax

Create a `.poly` file with language blocks:

```
global {
    x = 10
    message = "Hello"
}

python {
    y = x + 5
    print(f"Message: {message}, Y: {y}")
    export('py_result', y)
}

javascript {
    console.log(x);
    console.log(message);
}

c {
    #include <stdio.h>
    int main() {
        printf("Hello from C!\n");
        return 0;
    }
}

java {
    System.out.println("Hello from Java!");
}

c++ {
    #include <iostream>

    int main() {
        std::cout << "Hello from C++!" << std::endl;
        return 0;
    }
}
```

### Running

```bash
python poly.py script.poly
```

### Output Example

```
=== Running global ===

=== Running python ===
Message: Hello, Y: 15

=== Running javascript ===
10
Hello

=== Running c ===
Hello from C!

=== Running java ===
Hello from Java!

=== Running c++ ===
Hello from C++!
```

---

## Variable Sharing Overview

```
.poly File
    ↓
Parser (breaks into blocks)
    ↓
Interpreter (processes each block)
    ↓
┌────────────┬──────────────┬──────────┐
↓            ↓              ↓          ↓
Global       Python Let me provide a simpler structure
Runner       JS Runner     C Runner / C++ Runner / Java Runner
    ↓            ↓              ↓          ↓
    └────────────┴──────────────┴──────────┘
             Context
        (shared variables)
```

**How Variables Flow:**
1. **Global block** sets initial variables in Context
2. **Python block** reads from Context, can modify/add variables
3. **JavaScript block** receives variables as JSON serialized vars
4. **C**, **C++**, and **Java** blocks do not receive or share variables
5. Variables can be **exported** from languages back to Context

---

## Key Classes

### `BlockNode` (`core/ast.py`)
```python
BlockNode(language, code)
    - language: str (e.g., "python", "javascript", "js", "c", "c++", "cpp", "java")
    - code: str (source code for that language)
```

### `ProgramNode` (`core/ast.py`)
```python
ProgramNode(blocks)
    - blocks: list of BlockNode objects
```

### `Context` (`core/context.py`)
```python
Context()
    - set(key, value): Store variable
    - get(key): Retrieve variable
    - all(): Get all variables as dict
```

---

## Dependencies

- **Python 3.x** - For parsing and Python code execution
- **Node.js** - For JavaScript code execution
- **GCC** - For C code compilation
- **G++** - For C++ code compilation
- **JDK / `javac` + `java`** - For Java compilation and execution

Install Node.js, GCC/G++, and a JDK on your system for full functionality.

---

## Notes

- The **`global` block** is a special block for initializing shared variables
- **Variable names** starting with `__` are treated as internal and not shared
- **Python** can use `export(name, value)` to explicitly send variables back to Context
- **JavaScript** receives all context variables as `var` declarations
- **`js`** is supported as an alias for **`javascript`**
- **C**, **C++**, and **Java** are compiled and executed independently; cannot access context variables
- Blocks execute **sequentially** in the order they appear in the file

