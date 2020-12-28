import asyncio
import pytest
import pymongo
from asynctest.mock import CoroutineMock, Mock, patch
from kutana.storage import OptimisticLockException
from kutana.storages import MongoDBStorage


def make_mongodb_storage():
    with patch("kutana.storages.mongodb.AsyncIOMotorClient") as mc:
        collection = Mock()
        collection.update_one = CoroutineMock()
        collection.create_index = CoroutineMock()
        collection.find_one = CoroutineMock()
        collection.delete_one = CoroutineMock()
        mc.return_value = {"kutana": {"storage": collection}}
        return MongoDBStorage("mongo")


def test_mongodb_storage():
    storage = make_mongodb_storage()

    async def test():
        # Init storage
        await storage.init()
        storage.collection.create_index.assert_awaited()

        # Put without version
        assert await storage._put("key", {"val1": 1, "val2": 2}) == 1
        storage.collection.update_one.assert_awaited_with(
            {"_key": "key", "_version": 0},
            {"$set": {"val1": 1, "val2": 2, "_key": "key", "_version": 1}},
            upsert=True
        )

        # Put with version
        assert await storage._put("key", {"val1": 1, "val2": 2}, version=1) == 2
        storage.collection.update_one.assert_awaited_with(
            {"_key": "key", "_version": 1},
            {"$set": {"val1": 1, "val2": 2, "_key": "key", "_version": 2}},
            upsert=True
        )

        # Get value
        await storage._get("key")
        storage.collection.find_one.assert_awaited_with({"_key": "key"}, projection={"_key": 0, "_id": 0})

        # Delete value
        await storage._delete("key")
        storage.collection.delete_one.assert_awaited_with({"_key": "key"})

    asyncio.get_event_loop().run_until_complete(test())


def test_mongodb_storage_conflict():
    storage = make_mongodb_storage()
    storage.collection.update_one.side_effect = pymongo.errors.DuplicateKeyError('error')

    async def test():
        with pytest.raises(OptimisticLockException):
            await storage._put("key", {"val1": 1, "val2": 2})

    asyncio.get_event_loop().run_until_complete(test())
