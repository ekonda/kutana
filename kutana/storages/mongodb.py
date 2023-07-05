import pymongo
import pymongo.errors
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from ..storage import Document, OptimisticLockException, Storage


class MongoDBStorage(Storage):
    """
    Storage implementation of the storage that uses a running MongoDB server.
    """

    def __init__(self, mongodb_uri, database="kutana", collection="storage"):
        self._config = {"host": mongodb_uri, "database": database, "collection": collection}
        self.client: AsyncIOMotorClient
        self.database: AsyncIOMotorDatabase
        self.collection: AsyncIOMotorCollection

    async def init(self):
        self.client = AsyncIOMotorClient(self._config["host"])
        self.database = self.client[self._config["database"]]
        self.collection = self.database[self._config["collection"]]

    async def put(self, key, data):
        try:
            data = await self.collection.find_one_and_update(
                {
                    "_id": key,
                    "_version": data.get("_version"),
                },
                {
                    "$set": {
                        **{k: v for k, v in data.items() if v is not None},
                        "_id": key,
                        "_version": data.get("_version", 0) + 1,
                    },
                    "$unset": {
                        **{k: v for k, v in data.items() if v is None},
                    },
                },
                upsert=True,
                return_document=pymongo.ReturnDocument.AFTER,
            )

            data.pop("_id")  # Key should not be in resulting data

            return Document(data, _storage=self, _storage_key=key)
        except pymongo.errors.DuplicateKeyError:  # type: ignore
            raise OptimisticLockException(f'Failed to update data for key "{key}" (mismatched version)')

    async def get(self, key):
        data = await self.collection.find_one({"_id": key}, projection={"_id": 0})

        if data:
            return Document(data, _storage=self, _storage_key=key)

        return data

    async def delete(self, key):
        await self.collection.delete_one({"_id": key})
