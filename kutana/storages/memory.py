import random
from ..storage import Storage, OptimisticLockException


class MemoryStorage(Storage):
    """
    Naive implementation of the storage that uses in-memory dict for
    storing data.

    WARNING:
        When keys count is equal or greater than 'keys_limit', 30% of the
        stored keys will be cleared.
    """

    def __init__(self, keys_limit=1_000_000):
        self.keys_limit = keys_limit
        self._storage = {}

    async def _put(self, key, values, version=None):
        # handle keys overflow
        if len(self._storage) >= self.keys_limit:
            for key in random.sample(list(self._storage.keys()), k=int(self.keys_limit * 0.3)):
                self._storage.pop(key)

        # use optimistic locking
        if version is None and key in self._storage:
            raise OptimisticLockException("Values for this key already exists")

        if version is not None and key not in self._storage:
            raise OptimisticLockException("Values for this key was deleted")

        if self._storage.get(key, {}).get("_version") != version:
            raise OptimisticLockException("Versions differ from expected value")

        # update value
        new_version = (version or 0) + 1
        self._storage[key] = {**values, "_version": new_version}
        return new_version

    async def _get(self, key):
        return self._storage.get(key, None)

    async def _delete(self, key):
        self._storage.pop(key, None)
