from unittest.mock import patch

from mongomock_motor import AsyncMongoMockClient
from pytest import raises

from kutana.storage import DocumentIsDeletedException, OptimisticLockException, Storage
from kutana.storages import MemoryStorage, MongoDBStorage, SqliteStorage


async def _test_storage(storage: Storage):
    # Save data
    assert await storage.put("a", {"value": 1})
    assert await storage.put("b", {"value": 2})
    assert await storage.put("c", {"value": 3})

    # Load adta
    assert await storage.get("c") == {"_version": 1, "value": 3}
    assert await storage.get("b") == {"_version": 1, "value": 2}
    assert await storage.get("a") == {"_version": 1, "value": 1}

    # Update data
    doc = await storage.get("c")
    assert doc
    await doc.update_and_save({"value_cyr": 19})
    assert await storage.get("c") == {"_version": 2, "value": 3, "value_cyr": 19}

    # Delelte data
    assert await storage.delete("c") is None
    assert await storage.get("c") is None

    # Concurrency (1)
    d1 = await storage.put("d", {"value": 4})
    d2 = await storage.get("d")
    assert d2
    assert d1 == d2

    await d1.update_and_save({"value_cyr": 0})
    assert d1 != d2

    await d2.reload()
    assert d1 == d2

    await d1.delete()
    with raises(DocumentIsDeletedException):
        await d2.reload()
    with raises(DocumentIsDeletedException):
        await d1.reload()
    assert d1 == d2
    assert await storage.get("d") is None

    # Concurrency (2)
    d1 = await storage.put("d", {"value": 100})
    d2 = await storage.get("d")
    assert d2
    assert d1 == d2

    d1["value_cyr"] = 0
    await d1.save()

    d2["value_eng"] = d2["value"]
    with raises(OptimisticLockException):
        await d2.save()
    assert d1 != d2

    await d2.reload()
    assert "value_eng" not in d2
    d2["value_eng"] = d2["value"]
    await d2.save()

    assert d1 != d2

    await d1.reload()
    assert d1 == d2


async def test_memory_storage():
    storage = MemoryStorage()
    await storage.init()
    await _test_storage(storage)


async def test_sqlite_storage(tmp_path):
    storage = SqliteStorage(tmp_path / "storage.sqlite3")
    await storage.init()
    await _test_storage(storage)


async def test_mongo_storage():
    with patch("kutana.storages.mongodb.AsyncIOMotorClient", new=AsyncMongoMockClient):
        storage = MongoDBStorage("localhost")
        await storage.init()
        await _test_storage(storage)
