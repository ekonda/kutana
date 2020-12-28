from .helpers import ensure_list


class OptimisticLockException(Exception):
    pass


class Document:
    def __init__(self, values, key=None, storage=None):
        self.key = key
        self.storage = storage
        self.values = values

    @property
    def version(self):
        return self.values.get("_version", None)

    def __setattr__(self, key, value):
        if key in ("values", "key", "storage"):
            super().__setattr__(key, value)
        else:
            self.__dict__["values"][key] = value

    def __getattr__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __getitem__(self, key):
        return self.values[key]

    def __len__(self):
        return len(self.values)

    def __delitem__(self, key):
        del self.values[key]

    def __contains__(self, item):
        return item in self.values

    def __iter__(self):
        return iter(self.values)

    def __str__(self):
        return f"Document('{self.key}', {self.values})"

    async def update(self, values, remove=()):
        self.values.update(values)
        for field in ensure_list(remove):
            self.values.pop(field)
        return await self.save()

    async def save(self):
        """
        Save this document. Raises :class:`kutana.storage.OptimisticLockException` on
        issues with optimistic locking.
        """
        if not self.key:
            raise ValueError("This document missing a key")
        if not self.storage:
            raise ValueError("This document missing a storage")

        self.values["_version"] = await self.storage.put(self.key, self.values)

        return self

    async def refresh(self):
        """
        Load current data from the storage and replace current one with it.
        """
        current = await self.storage.get(self.key)
        if not current:
            raise ValueError("This document is deleted now")

        self.values = current.values

        return self


class Storage:
    async def init(self):
        pass

    def make_document(self, values, key):
        return Document({**values, "_version": None}, key=key, storage=self)

    async def put(self, key, values):
        if "_version" not in values:
            raise ValueError("Values missing '_version'")
        return await self._put(key, values, version=values.get("_version"))

    async def delete(self, key):
        return await self._delete(key)

    async def get(self, key):
        values = await self._get(key)
        if not values:
            return None
        return Document(values, key=key, storage=self)

    async def _put(self, key, values, version=None):
        raise NotImplementedError

    async def _get(self, key):
        raise NotImplementedError

    async def _delete(self, key):
        raise NotImplementedError
