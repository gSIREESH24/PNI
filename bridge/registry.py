from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FunctionEntry:
    """Metadata for a function registered in the global bridge registry."""
    name:        str
    language:    str
    func:        Any   = None              # callable — for Python-owned functions
    param_types: list  = field(default_factory=list)
    return_type: Optional[str] = None
    # ── Milestone 3 stub fields ──────────────────────────────────────────────
    stub_source: Optional[str] = None     # full source code for subprocess fns


class Registry:
    """
    The single, shared registry for the Phase-2/3 bridge.
    Stores:
      - values    : name → raw Python value (ints, strings, bools, floats, …)
      - functions : name → FunctionEntry (owner language + callable OR stub source)

    Python-owned functions are directly callable via entry.func.
    Subprocess-language functions are re-invoked via stub_invoker using entry.stub_source.
    """

    def __init__(self):
        self.values:        dict[str, Any]            = {}
        self.functions:     dict[str, FunctionEntry]  = {}
        self.class_schemas: dict[str, dict[str, str]] = {}

    # ── Classes (Phase 3D) ────────────────────────────────────────────────────

    def export_class_schema(self, name: str, fields: dict[str, str]):
        """
        Store a class schema structure. 
        fields is a dict mapping field_name -> type_string ('int', 'float', 'str', 'bool')
        """
        self.class_schemas[name] = fields

    # ── Values ────────────────────────────────────────────────────────────────

    def set_value(self, name: str, value: Any):
        self.values[name] = value

    def get_value(self, name: str, default=None):
        return self.values.get(name, default)

    # ── Python-owned functions ────────────────────────────────────────────────

    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type: str = None):
        self.functions[name] = FunctionEntry(
            name=name,
            language=language,
            func=func,
            param_types=param_types or [],
            return_type=return_type,
        )

    # ── Subprocess function stubs (Milestone 3) ───────────────────────────────

    def register_stub(self, name: str, language: str, source: str,
                      return_type: str = "int"):
        """Register a function whose implementation lives in a subprocess language."""
        self.functions[name] = FunctionEntry(
            name=name,
            language=language,
            func=None,
            return_type=return_type,
            stub_source=source,
        )

    # ── Lookup ────────────────────────────────────────────────────────────────

    def get_function(self, name: str) -> Optional[FunctionEntry]:
        return self.functions.get(name)

    def has_function(self, name: str) -> bool:
        return name in self.functions

    def list_functions(self) -> list[str]:
        return list(self.functions.keys())