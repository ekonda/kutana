"""Base for managers."""

class BasicManager:  # pragma: no cover
    """Base for manager."""

    type = "basic"

    async def get_environment(self, update):
        """
        Create and return manager's environment for update processing.

        :param update: manager's service raw update
        :rtype: Environment for manager's service
        """

        raise NotImplementedError

    async def convert_to_message(self, update):
        """
        Create and return :class:`.Message` from raw_update.

        :param update: manager's service raw update
        :rtype: :class:`.Message` or None if message can't be created
        """

        raise NotImplementedError

    async def get_background_coroutines(self, ensure_future):
        """
        Collect background coroutines for Kutana to run.

        :param ensure_future: kutana's wrapper for asyncio.ensure_future
        :rtype: list of tasks to be executed in background in Kutana
        """

        raise NotImplementedError

    async def get_receiver_coroutine_function(self):
        """
        Collect coroutine for receiving updated from service.

        :rtype: coroutine for receiving updated from service
        """

        raise NotImplementedError

    async def dispose(self):
        """Free used resources."""

        raise NotImplementedError
