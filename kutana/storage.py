from typing import Dict, Optional


class OptimisticLockException(Exception):
    pass


class DocumentIsDeletedException(Exception):
    pass


class Document(dict):
    def __init__(self, *args, _storage: "Storage", _storage_key: str, **kwargs):
        self._storage = _storage
        self._storage_key = _storage_key
        super().__init__(*args, **kwargs)

    async def save(self):
        self.update(await self._storage.put(self._storage_key, self))

    async def update_and_save(self, *args, **kwargs):
        self.update(*args, **kwargs)
        await self.save()

    async def reload(self):
        data = await self._storage.get(self._storage_key)
        if data is None:
            raise DocumentIsDeletedException("Value being reloaded is deleted")
        self.clear()
        self.update(data)

    async def delete(self):
        await self._storage.delete(self._storage_key)


class Storage:
    async def init(self):
        pass

    async def put(self, key: str, data: Dict) -> Document:
        raise NotImplementedError

    async def get(self, key: str) -> Optional[Document]:
        raise NotImplementedError

    async def delete(self, key: str):
        raise NotImplementedError
