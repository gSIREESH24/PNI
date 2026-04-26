"""
bridge/__init__.py — Public API of the PLF bridge package.

Everything outside this package should import from here.
Internal file layout:

  bridge.py           — Bridge (main hub, owns registry + store + dispatcher)
  function_registry.py— FunctionRegistry + FunctionEntry
  object_store.py     — ObjectStore (handle-based object storage)
  dispatcher.py       — Dispatcher (routes calls to Python fn or native stub)
  stub_runner.py      — invoke() (re-executes native stubs on demand)
  protocol.py         — run_subprocess() + wire-protocol constants & codecs
  value_types.py      — PolyType + PolyValue (cross-language type system)
"""

from .bridge           import Bridge
from .function_registry import FunctionRegistry, FunctionEntry
from .object_store     import ObjectStore
from .dispatcher       import Dispatcher
from .protocol         import run_subprocess, encode_return, decode_return
from .value_types      import PolyType, PolyValue

__all__ = [
    "Bridge",
    "FunctionRegistry",
    "FunctionEntry",
    "ObjectStore",
    "Dispatcher",
    "run_subprocess",
    "encode_return",
    "decode_return",
    "PolyType",
    "PolyValue",
]