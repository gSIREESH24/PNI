from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FunctionEntry:
    """Metadata for a function registered in the global bridge registry."""
    name: str
    language: str
    func: Any                            # callable for Python; None for subprocess languages
    param_types: list = field(default_factory=list)
    return_type: Optional[str] = None


class Registry:
    """
    The single, shared registry for the Phase-2 bridge.
    Stores:
      - values  : name → raw Python value (ints, strings, bools, floats, …)
      - functions : name → FunctionEntry (owner language + callable handle)

    Any language can read values; only Python functions are directly callable.
    Subprocess languages (JS, C, C++, Java) receive values via code injection
    and export results through stdout markers.
    """

    def __init__(self):
        self.values: dict[str, Any] = {}
        self.functions: dict[str, FunctionEntry] = {}

    # ── Values ────────────────────────────────────────────────────────────

    def set_value(self, name: str, value: Any):
        self.values[name] = value

    def get_value(self, name: str, default=None):
        return self.values.get(name, default)

    # ── Functions ─────────────────────────────────────────────────────────

    def export_function(self, name: str, func, language: str = "python",
                        param_types=None, return_type: str = None):
        self.functions[name] = FunctionEntry(
            name=name,
            language=language,
            func=func,
            param_types=param_types or [],
            return_type=return_type,
        )

    def get_function(self, name: str) -> Optional[FunctionEntry]:
        return self.functions.get(name)

    def has_function(self, name: str) -> bool:
        return name in self.functions

    def list_functions(self) -> list[str]:
        return list(self.functions.keys())