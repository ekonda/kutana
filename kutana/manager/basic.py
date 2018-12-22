class BasicManager:  # pragma: no cover
    type = "basic"

    async def get_environment(self, update):
        """Create and return manager's environment for update processing."""

        raise NotImplementedError

    async def convert_to_message(self, update):
        """Convert raw update to instances of :class:`.Message`
        and :class:`.Attachmnet` for plugins.
        """

        raise NotImplementedError

    async def get_background_coroutines(self, ensure_future):
        """Return list of tasks to be executed in background in Kutana."""

        raise NotImplementedError

    async def get_receiver_coroutine_function(self):
        """Return coroutine function for getting updates from vk.com."""

        raise NotImplementedError

    async def dispose(self):
        """Free used resources."""

        raise NotImplementedError
