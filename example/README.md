# 📂 Polyglot Cross-Language Example Suite

This directory contains **20+ robust executable `.poly` files**, each demonstrating a highly specific capability of the Polyglot Bridge runtime, spanning across Python, JavaScript, C, C++, and Java.

## Running an Example

To test an example, make sure you are in the project's root folder and dispatch it via the CLI:
```bash
python poly.py example/19_universal_vice_versa.poly
```

---

## The Suite Index

| Example File | What Features It Demonstrates |
|---|---|
| `01_globals.poly` | Defining strongly-typed shared global variables. |
| `02_python_export.poly` | Registering exports cleanly in Python strings. |
| `03_python_function_bridge.poly` | Registering native callables across the internal bridge dispatcher. |
| `04_python_to_js.poly` | Bridging heavily nested objects from Python memory securely into the Node.js process. |
| `05_python_to_c.poly` | Generating native `static const` macros bridging Python to GCC templates. |
| `06_python_to_cpp.poly` | Transpiling native variables to the g++ subprocess workspace. |
| `07_python_to_java.poly` | Emitting native static Java fields for JDK block compilations. |
| `08_all_types.poly` | Securely shuttling `int`, `float`, `bool`, and `string` interchangeably between all 5 runtimes. |
| `09_string_operations.poly` | Memory safe escaped string concatenation passed across all language pipelines. |
| `10_math_chain.poly` | Demonstrating intense multi-subprocess state synchronization over 5 blocks. |
| `11_counter_accumulator.poly` | Reading, modifying, and tracking a shifting global counter progressively modified by each language iteratively. |
| `12_boolean_flags.poly` | Complex boolean evaluation loops spanning subprocess bounds. |
| `13_full_pipeline.poly` | The ultimate cross-stack pipeline utilizing all languages simultaneously. |
| `14_object_handles.poly` | Passing Python instantiated `dict/class` items off to unmanaged runtimes using mapped handle IDs. |
| `15_py_fn_to_all.poly` | Letting all C, C++, Node, and JVM subprocesses simultaneously invoke a single Python host function. |
| `16_any_fn_to_python.poly` | Letting a C++ process register its logic off for Python execution bounds. |
| `17_class_schema_bridge.poly` | Using the class generation engine to duplicate Python Object blueprints directly into native structs/classes. |
| `18_method_proxy_bridge.poly` | Passing Handle IDs across barriers so C and Java can dynamically execute properties on Python instantiated components. |
| `19_universal_vice_versa.poly` | **True polyglot recursive stubbing**: JS spawns C, C spawns Python, Python spawns Java effortlessly. |

> **Temporary Run Files**: All executions (C bounds, Java class outputs) are compiled entirely inside the OS hidden `/Temp/` directory, keeping this project folder pristine!
