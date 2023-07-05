import random
from typing import Optional
from threading import Lock

from ..storage import OptimisticLockException, Document, Storage


class MemoryStorage(Storage):
    """
    Naive implementation of the storage that uses in-memory dict for
    storing data.

    WARNING:
        When keys count is equal or greater than 'keys_limit', 30% of the
        stored keys will be cleared.
    """

    def __init__(self, keys_limit=1_000_000):
        self._keys_limit = keys_limit
        self._storage = {}
        self._lock = Lock()

    def _get_document(self, data, key) -> Optional[Document]:
        if data:
            return Document(data, _storage=self, _storage_key=key)
        return data

    async def put(self, key, data):
        with self._lock:
            # handle keys limit overflow
            if len(self._storage) >= self._keys_limit:
                for key in random.sample(list(self._storage.keys()), k=int(self._keys_limit * 0.3)):
                    self._storage.pop(key)

            # use optimistic locking
            if not data.get("_version") and key in self._storage:
                raise OptimisticLockException("Data for this key already exists")

            if data.get("_version") and key not in self._storage:
                raise OptimisticLockException("Data for this key was deleted")

            if data.get("_version") != self._storage.get(key, {}).get("_version"):
                raise OptimisticLockException("Data version differ from the expected value")

            # process data and save it
            document = {
                **{k: v for k, v in data.items() if v is not None},
                "_version": (data.get("_version") or 0) + 1,
            }

            self._storage[key] = document

            return self._get_document(document, key)

    async def get(self, key):
        with self._lock:
            return self._get_document(self._storage.get(key, None), key)

    async def delete(self, key):
        with self._lock:
            self._storage.pop(key, None)
