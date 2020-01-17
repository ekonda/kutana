from ..storage import Storage


class NaiveMemory(Storage):
    """
    Storage for storing data with naive approach. It uses only memory
    and will wipe some portion of stored data when number of keys
    will react certain amount.

    It's not persistent and not safe. It's here for tiny projects
    and debugging.
    """

    def __init__(self, max_size=2000000):
        self._storage = {}
        self.max_size = max_size

    async def save(self, name, value):
        if len(self._storage) >= self.max_size:
            keys = list(self._storage.keys())

            for k in keys[:self.max_size // 2]:
                self._storage.pop(k)

        self._storage[name] = value

    async def load(self, name, default=None):
        return self._storage.get(name, default)
