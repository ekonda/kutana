import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
from ..storage import Storage, OptimisticLockException


class MongoDBStorage(Storage):
    """
    Storage implementation of the storage that uses running MongoDB server.
    """

    def __init__(self, mongodb_uri, database="kutana", collection="storage"):
        self._config = {"host": mongodb_uri, "database": database, "collection": collection}
        self.client = None
        self.database = None
        self.collection = None

    async def init(self):
        self.client = AsyncIOMotorClient(self._config["host"])
        self.database = self.client[self._config["database"]]
        self.collection = self.database[self._config["collection"]]
        await self.collection.create_index([("_key", pymongo.ASCENDING)], unique=True)

    async def _put(self, key, values, version=None):
        new_version = (version or 0) + 1

        try:
            await self.collection.update_one(
                {"_key": key, "_version": version or 0},
                {"$set": {
                    **values,
                    "_key": key,
                    "_version": new_version,
                }},
                upsert=True
            )
        except pymongo.errors.DuplicateKeyError:
            raise OptimisticLockException(f"Failed to set values for key {key} (mismatched version)")

        return new_version

    async def _get(self, key):
        return await self.collection.find_one({"_key": key}, projection={"_key": 0, "_id": 0})

    async def _delete(self, key):
        await self.collection.delete_one({"_key": key})
