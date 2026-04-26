from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FunctionEntry:
    name:        str
    language:    str
    func:        Any            = None
    param_types: list           = field(default_factory=list)
    return_type: Optional[str]  = None
    stub_source: Optional[str]  = None


class FunctionRegistry:

    def __init__(self):
        self.values:        dict[str, Any]            = {}
        self.functions:     dict[str, FunctionEntry]  = {}
        self.class_schemas: dict[str, dict[str, str]] = {}

    def set_value(self, name: str, value: Any):
        self.values[name] = value

    def get_value(self, name: str, default=None):
        return self.values.get(name, default)

    def register_class_schema(self, name: str, fields: dict[str, str]):
        self.class_schemas[name] = fields

    def register_python_function(self, name: str, func,
                                 param_types=None, return_type: str = None):
        self.functions[name] = FunctionEntry(
            name=name, language="python", func=func,
            param_types=param_types or [], return_type=return_type,
        )

    def register_stub(self, name: str, language: str, source: str,
                      return_type: str = "int"):
        self.functions[name] = FunctionEntry(
            name=name, language=language, func=None,
            return_type=return_type, stub_source=source,
        )

    def get_function(self, name: str) -> Optional[FunctionEntry]:
        return self.functions.get(name)

    def has_function(self, name: str) -> bool:
        return name in self.functions

    def list_functions(self) -> list[str]:
        return list(self.functions.keys())
