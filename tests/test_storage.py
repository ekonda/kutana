import asyncio
from kutana.storages import NaiveMemory


def test_naive_memory_storage():
    async def test():
        storage = NaiveMemory()

        await storage.save("key1", "value1")
        await storage.save("key2", "value2")

        assert await storage.load("key1") == "value1"
        assert await storage.load("key2") == "value2"
        assert await storage.load("key3") is None
        assert await storage.load("key4", "bruh") == "bruh"

    asyncio.get_event_loop().run_until_complete(test())


def test_naive_memory_overflow():
    async def test():
        storage = NaiveMemory(max_size=100)

        for i in range(100):
            await storage.save(f"key{i}", "val")

        await storage.save(f"overflow", "val")

        assert len(storage._storage) == 51

    asyncio.get_event_loop().run_until_complete(test())
