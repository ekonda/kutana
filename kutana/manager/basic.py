"""Base for managers."""


class BasicManager:

    """Base for manager."""

    type = "basic"

    @staticmethod
    def split_large_text(text):
        """
        Split text into chunks with length of 4096.

        :param text: text for splitting
        :rtype: tuple of chunks
        """

        if len(text) < 4096:
            return (text,)

        return tuple(
            text[i : i + 4096] for i in range(0, len(text), 4096)
        )

    async def get_environment(self, update):
        """
        Create and return manager's environment for update processing.

        :param update: manager's service raw update
        :rtype: Environment for manager's service
        """

        raise NotImplementedError

    async def create_message(self, update):
        """
        Create and return :class:`.Message` from raw_update.

        :param update: manager's service raw update
        :rtype: :class:`.Message` or None if message can't be created
        """

        raise NotImplementedError

    async def request(self, method, **kwargs):
        """
        Perform request to manager's service and return result.

        :rtype: response
        """

        raise NotImplementedError

    async def send_message(self, message, peer_id, attachment=None, **kwargs):
        """
        Send message to target user with "peer_id" with parameters. This can
        vary in managers' implementations.

        :param message: text to send
        :param peer_id: target recipient
        :param attachment: list of instances of :class:`.Attachment`
        :parma kwargs: arguments to send to manager's methods
        :rtype: list of responses
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
