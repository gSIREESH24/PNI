"""
object_store.py — Handle-based storage for non-primitive Python objects.

Instead of trying to pass rich Python objects across language boundaries,
we store them here and share only an opaque integer handle.
Other languages receive the handle as a plain number and call back
via __POLY_METHOD__ to invoke methods on the stored object.
"""


class ObjectStore:
    """Integer-keyed store for arbitrary Python objects."""

    def __init__(self):
        self._objects: dict[int, object] = {}
        self._next_id: int = 1

    def put(self, obj) -> int:
        """Store an object and return its handle."""
        handle = self._next_id
        self._objects[handle] = obj
        self._next_id += 1
        return handle

    def get(self, handle: int):
        """Retrieve an object by handle, or None if not found."""
        return self._objects.get(handle)

    def delete(self, handle: int):
        """Remove an object from the store."""
        self._objects.pop(handle, None)

    def __len__(self):
        return len(self._objects)