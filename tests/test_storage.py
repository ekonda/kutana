import asyncio
import pytest
from kutana.storage import Document, OptimisticLockException
from kutana.storages import MemoryStorage


def test_document_interactions():
    doc = Document({"key1": "val1", "_version": 1})

    assert doc.version == 1
    assert doc["key1"] == "val1"

    doc.key2 = "val2"
    doc["key3"] = "val3"

    assert doc.key2 == "val2"
    assert doc["key3"] == "val3"
    assert len(doc) == 4

    del doc["key2"]
    del doc["key3"]

    assert "key2" not in doc
    assert "key3" not in doc
    assert [k for k in doc] == ["key1", "_version"]

    assert str(doc.values) in str(doc)


def test_document_ops():
    storage = MemoryStorage()

    async def test():
        doc = storage.make_document({"key1": "val1", "_version": 1}, key="123")
        await doc.save()

        assert storage._storage["123"]
        storage._storage["123"]["key2"] = "val2"

        await doc.refresh()
        assert doc["key2"] == "val2"

        await doc.update({"key3": "val3"}, remove=["key2"])
        assert doc["key3"] == "val3"
        assert "key2" not in doc

        await storage.delete(doc.key)
        assert "123" not in storage._storage

    asyncio.get_event_loop().run_until_complete(test())


def test_document_exceptions():
    storage = MemoryStorage()

    async def test():
        doc = storage.make_document({"key1": "val1", "_version": 1}, key="123")

        with pytest.raises(ValueError):
            await doc.refresh()

        doc.storage =  None

        with pytest.raises(ValueError):
            await doc.save()

        doc.key =  None
        doc.storage = storage

        with pytest.raises(ValueError):
            await doc.save()

    asyncio.get_event_loop().run_until_complete(test())


def test_storage_exceptions():
    storage = MemoryStorage()

    async def test():
        with pytest.raises(ValueError):
            await storage.put('123', {})

    asyncio.get_event_loop().run_until_complete(test())


def test_memory_storage():
    storage = MemoryStorage(10)

    async def test():
        doc = await storage.make_document({}, 'key').save()

        with pytest.raises(OptimisticLockException):
            await storage.make_document({}, 'key').save()

        await storage.delete('key')

        with pytest.raises(OptimisticLockException):
            await doc.save()

        doc_1 = await storage.make_document({}, 'key').save()
        doc_2 = await storage.get('key')

        with pytest.raises(OptimisticLockException):
            await doc_1.update({'key': 'value1'})
            await doc_2.update({'key': 'value2'})

    asyncio.get_event_loop().run_until_complete(test())

def test_memory_storage_limit():
    storage = MemoryStorage(10)

    async def test():
        for i in range(20):
            await storage.make_document({}, i + 1).save()

        assert len(storage._storage) == 8

    asyncio.get_event_loop().run_until_complete(test())
