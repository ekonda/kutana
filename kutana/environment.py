"""Base environment for manager."""

import types


class Environment:

    """Base environment for manager."""

    __slots__ = (
        "manager", "parent", "peer_id", "exception",
        "_has_message", "_message",
        "__dict__"
    )

    def __init__(self, manager, parent_environment=None, peer_id=None):
        self.manager = manager
        self.parent = parent_environment

        self.peer_id = peer_id

        self.exception = None

        self._has_message = None
        self._message = None

    def replace_method(self, method_name, method):
        """
        Replaces this instance's method with specified name with passed method

        Example:

        .. code-block:: python

            async def replacement(self, message):
                print(message)

            env = Environment(manager)
            env.replace_method("reply", replacement)
            await env.reply("hey")  # will print "hey"

        .. note::

            Many methods are coroutine, so you should replace coroutines with
            coroutines and normal functions with functions.

        :param method_name: method's name to replace
        :param method: method to replace with
        """

        self.__setattr__(method_name, types.MethodType(method, self))

    @property
    def manager_type(self):
        """Return currently processed message's manager type."""

        return self.manager.type

    def spawn(self):
        """
        Create partial copy of environment with this environment as parent.
        """

        return self.__class__(
            manager=self.manager,
            parent_environment=self,
            peer_id=self.peer_id
        )

    def has_message(self):
        """
        Return True if message was created from update
        (successfully or not).
        """

        return self._has_message

    def get_message(self):
        """Return currently processed message."""

        return self._message

    def set_message(self, message):
        """
        Change message that will be passed to every sequential callbacks'
        calls. Message should be instance of :class:`.Message`
        """

        self._message = message
        self._has_message = message is not None

    async def request(self, method, **kwargs):
        """Proxy for manager's "request" method."""

        return await self.manager.request(
            method, **kwargs
        )

    async def send_message(self, message, peer_id, attachment=None, **kwargs):
        """Proxy for manager's "send_message" method."""

        return await self.manager.send_message(
            message, peer_id, attachment, **kwargs
        )

    async def reply(self, message, attachment=None, **kwargs):
        """
        Reply to currently processed message.

        :param message: message to reply with
        :param attachment: optional attachment or list of attachments
        :param kwargs: arguments for request to service
        :rtype: list with results of sending messages
        """

        return await self.manager.send_message(
            message, self.peer_id, attachment, **kwargs
        )

    async def upload_doc(self, file, **kwargs):
        """
        Upload of prepare file to be sent with :func:`.send_message`
        (or :func:`.reply`) as document. This can vary in managers'
        implementations.

        :param file: document as file or bytes
        :param kwargs: arguments for manager's method
        :rtype: :class:`.Attachment` or None
        """

        raise NotImplementedError

    async def upload_photo(self, file, **kwargs):
        """
        Upload of prepare file to be sent with :func:`.send_message`
        (or :func:`.reply`) as photo. This can vary in managers'
        implementations.

        :param file: photo as file or bytes
        :param kwargs: arguments for manager's method
        :rtype: :class:`.Attachment` or None
        """

        raise NotImplementedError

    async def get_file_from_attachment(self, attachment):
        """
        Try to download passed attachment and return it as bytes. Return None
        if error occured.

        :param attachment: :class:`.Attachment`
        :rtype: bytes or None
        """

        raise NotImplementedError
