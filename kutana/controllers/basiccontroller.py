class BasicController:  # pragma: no cover
    TYPE = "basic"

    async def create_tasks(self, ensure_future):
        """Create tasks to be executed in background in Kutana."""

        raise NotImplementedError

    async def create_receiver(self):
        """Create coroutine function for getting updates from vk.com."""

        raise NotImplementedError

    async def dispose(self):
        """Free used resourses."""

        raise NotImplementedError
