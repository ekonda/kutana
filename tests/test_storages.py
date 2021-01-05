import asyncio
import functools
import pytest
import pymongo
from asynctest.mock import CoroutineMock, Mock, patch
from kutana.storage import OptimisticLockException
from kutana.storages import MongoDBStorage, SqliteStorage


# --- Test mongodb storage using mocks ---
def with_mongodb_storage(coro):
    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        with patch("kutana.storages.mongodb.AsyncIOMotorClient") as client:
            collection = Mock()
            collection.update_one = CoroutineMock()
            collection.create_index = CoroutineMock()
            collection.find_one = CoroutineMock()
            collection.delete_one = CoroutineMock()
            client.return_value = {"kutana": {"storage": collection}}
            return await coro(*args, storage=MongoDBStorage("mongo"), **kwargs)
    return wrapper


def test_mongodb_storage():
    @with_mongodb_storage
    async def test(storage):
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
    @with_mongodb_storage
    async def test(storage):
        await storage.init()

        storage.collection.update_one.side_effect = pymongo.errors.DuplicateKeyError('error')

        with pytest.raises(OptimisticLockException):
            await storage._put("key", {"val1": 1, "val2": 2})

    asyncio.get_event_loop().run_until_complete(test())


# --- Test sqlite storage using in-memory database ---
def with_sqlite_storage(coro):
    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        return await coro(*args, storage=SqliteStorage(":memory:"), **kwargs)
    return wrapper


def test_sqlite_storage():
    @with_sqlite_storage
    async def test(storage):
        await storage.init()
        assert await storage._put("key", {"val1": 1, "val2": 2}) == 1
        assert await storage._put("key", {"val1": 1, "val2": 2}, version=1) == 2
        with pytest.raises(OptimisticLockException):
            await storage._put("key", {"val1": 1, "val2": 3}, version=1)
        assert await storage._get("key") == {"val1": 1, "val2": 2, "_version": 2}
        await storage._delete("key")
        assert await storage._get("key") is None

    asyncio.get_event_loop().run_until_complete(test())
