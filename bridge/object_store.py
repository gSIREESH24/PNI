class ObjectStore:
    """
    Handle-based storage for non-primitive objects.

    Instead of passing raw Python objects across language boundaries,
    we store them here and pass only an integer handle ID.
    This is safe, language-agnostic, and maps to the JNI jobject idea.

    Usage:
        handle = store.put(my_object)   # returns int handle
        obj    = store.get(handle)      # retrieves the object
        store.delete(handle)            # releases it
    """

    def __init__(self):
        self._store: dict[int, object] = {}
        self._next_id: int = 1

    def put(self, obj) -> int:
        handle = self._next_id
        self._store[handle] = obj
        self._next_id += 1
        return handle

    def get(self, handle: int):
        return self._store.get(handle)

    def delete(self, handle: int):
        self._store.pop(handle, None)

    def __len__(self):
        return len(self._store)