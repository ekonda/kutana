"""Base for managers."""


class Manager():

    """Base for manager."""

    _type = ""

    def get_type(self):
        """Return this manager's type."""

        return self._type

    @staticmethod
    def split_large_text(text):
        """
        Split text into chunks with length of 4096.

        :param text: text for splitting
        :returns: tuple of chunks
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
        :returns: :class:`.Environment` for manager's service
        """

        raise NotImplementedError

    async def create_message(self, update):
        """
        Create and return :class:`.Message` from raw_update.

        :param update: manager's service raw update
        :returns: :class:`.Message` or None if message can't be created
        """

        raise NotImplementedError

    async def request(self, method, **kwargs):
        """
        Perform request to manager's service and return result.

        :returns: response
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
        :returns: list of responses
        """

        raise NotImplementedError

    async def get_receiver_coroutine_function(self):
        """
        Collect coroutine for receiving updated from service.

        :returns: coroutine for receiving updated from service
        """

        raise NotImplementedError

    async def startup(self, application):
        """
        Start coroutines and prepare everything else needed for
        manager to work.

        :param app: application
        """

        raise NotImplementedError

    async def dispose(self):
        """Free used resources."""

        raise NotImplementedError
