class ObjectStore:

    def __init__(self):
        self._objects: dict[int, object] = {}
        self._next_id: int = 1

    def put(self, obj) -> int:
        handle = self._next_id
        self._objects[handle] = obj
        self._next_id += 1
        return handle

    def get(self, handle: int):
        return self._objects.get(handle)

    def delete(self, handle: int):
        self._objects.pop(handle, None)

    def __len__(self):
        return len(self._objects)