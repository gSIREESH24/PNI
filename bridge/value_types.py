"""
value_types.py — Shared type system for the PLF bridge.

PolyType  : enum of every type that can cross a language boundary.
PolyValue : a typed wrapper around a plain Python value.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PolyType(Enum):
    NULL     = "null"
    INT      = "int"
    FLOAT    = "float"
    BOOL     = "bool"
    STRING   = "string"
    ARRAY    = "array"
    OBJECT   = "object"
    FUNCTION = "function"
    ERROR    = "error"


@dataclass
class PolyValue:
    """A value tagged with its cross-language type."""

    type:  PolyType
    value: Any = None

    @staticmethod
    def null():
        return PolyValue(PolyType.NULL, None)

    @staticmethod
    def from_python(value):
        if value is None:           return PolyValue.null()
        if isinstance(value, bool): return PolyValue(PolyType.BOOL,     value)
        if isinstance(value, int):  return PolyValue(PolyType.INT,      value)
        if isinstance(value, float):return PolyValue(PolyType.FLOAT,    value)
        if isinstance(value, str):  return PolyValue(PolyType.STRING,   value)
        if isinstance(value, list): return PolyValue(PolyType.ARRAY,    [PolyValue.from_python(v) for v in value])
        if callable(value):         return PolyValue(PolyType.FUNCTION, value)
        return PolyValue(PolyType.OBJECT, value)

    def to_python(self):
        if self.type == PolyType.NULL:  return None
        if self.type == PolyType.ARRAY: return [v.to_python() if isinstance(v, PolyValue) else v for v in self.value]
        return self.value

    def __repr__(self):
        return f"PolyValue({self.type.value}, {self.value!r})"
