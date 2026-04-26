"""
function_registry.py — Global table of all functions known to the PLF bridge.

Stores two kinds of entries:
  - Python-owned : a live callable (entry.func is set).
  - Subprocess stub : source code in another language (entry.stub_source is set).
    These are re-executed on demand via stub_runner.py.

Also stores shared scalar values and cross-language class schemas.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FunctionEntry:
    """Metadata for one function registered in the bridge."""

    name:        str
    language:    str
    func:        Any            = None     # live callable (Python-owned)
    param_types: list           = field(default_factory=list)
    return_type: Optional[str]  = None
    stub_source: Optional[str]  = None    # native source for subprocess stubs


class FunctionRegistry:
    """
    The shared global lookup table for the PLF bridge.

    Holds:
      values        : name → plain Python scalar (int, float, bool, str, …)
      functions     : name → FunctionEntry
      class_schemas : name → {field: type_str} — forwarded to language adapters
    """

    def __init__(self):
        self.values:        dict[str, Any]            = {}
        self.functions:     dict[str, FunctionEntry]  = {}
        self.class_schemas: dict[str, dict[str, str]] = {}

    # ── Shared values ─────────────────────────────────────────────────────────

    def set_value(self, name: str, value: Any):
        self.values[name] = value

    def get_value(self, name: str, default=None):
        return self.values.get(name, default)

    # ── Class schemas ─────────────────────────────────────────────────────────

    def register_class_schema(self, name: str, fields: dict[str, str]):
        """Store a struct/class layout so language adapters can generate native code."""
        self.class_schemas[name] = fields

    # ── Python-owned functions ────────────────────────────────────────────────

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type: str = None):
        self.functions[name] = FunctionEntry(
            name=name, language="python", func=func,
            param_types=param_types or [], return_type=return_type,
        )

    # ── Subprocess stubs ──────────────────────────────────────────────────────

    def register_stub(self, name: str, language: str, source: str,
                      return_type: str = "int"):
        """Register a function whose body lives in a subprocess language."""
        self.functions[name] = FunctionEntry(
            name=name, language=language, func=None,
            return_type=return_type, stub_source=source,
        )

    # ── Lookup ────────────────────────────────────────────────────────────────

    def get_function(self, name: str) -> Optional[FunctionEntry]:
        return self.functions.get(name)

    def has_function(self, name: str) -> bool:
        return name in self.functions

    def list_functions(self) -> list[str]:
        return list(self.functions.keys())
