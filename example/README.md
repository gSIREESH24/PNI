# Phase-2 Polyglot Examples Index

Each `.poly` file in this directory demonstrates a specific capability of the bridge.

Run any example with:
```bash
python poly.py example/<filename>.poly
```

---

## Examples

| File | What It Demonstrates |
|---|---|
| `01_globals.poly` | Defining and reading shared global variables |
| `02_python_export.poly` | Python exporting values and functions |
| `03_python_function_bridge.poly` | Python-to-Python function call through the bridge |
| `04_python_to_js.poly` | Python exports, JavaScript reads and responds |
| `05_python_to_c.poly` | Python exports, C reads and responds |
| `06_python_to_cpp.poly` | Python exports, C++ reads and responds |
| `07_python_to_java.poly` | Python exports, Java reads and responds |
| `08_all_types.poly` | int, float, bool, string sharing across all languages |
| `09_string_operations.poly` | String values passed between all 5 languages |
| `10_math_chain.poly` | Mathematical computation chained across all languages |
| `11_counter_accumulator.poly` | Running counter incremented by each language |
| `12_boolean_flags.poly` | Boolean flags set and read across languages |
| `13_full_pipeline.poly` | Complete data pipeline — all languages in sequence |
| `14_object_handles.poly` | Python object stored by handle, retrieved by handle |
