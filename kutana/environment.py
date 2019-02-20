"""Base environment for manager."""

import functools


class Environment:

    """Base environment for manager."""

    __slots__ = (
        "manager", "parent", "peer_id",
        "_has_message", "_message",
        "_replaced_methods", "_storage"
    )

    def __init__(self, manager, parent_environment=None, peer_id=None):
        self.manager = manager
        self.parent = parent_environment

        self.peer_id = peer_id

        self._replaced_methods = {}
        self._has_message = None
        self._message = None
        self._storage = {}

    def __setattr__(self, name, value):
        if name in object.__getattribute__(self, "__slots__"):
            object.__setattr__(self, name, value)

        elif name in dir(self):
            raise AttributeError

        else:
            self._storage[name] = value

    def __getattribute__(self, name):
        replaced_methods = object.__getattribute__(self, "_replaced_methods")

        if name in replaced_methods:
            return functools.partial(replaced_methods[name], self)

        storage = object.__getattribute__(self, "_storage")

        if name in storage:
            return storage[name]

        return object.__getattribute__(self, name)

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

        if method_name not in dir(self) \
                or not callable(getattr(self, method_name)):

            raise ValueError("No method with name '{}'".format(method_name))

        self._replaced_methods[method_name] = method

    @property
    def manager_type(self):
        """Return currently processed message's manager type."""

        return self.manager.type

    def spawn(self):
        """
        Create partial copy of environment with this environment as parent.
        """

        new_env = self.__class__(
            manager=self.manager,
            parent_environment=self,
            peer_id=self.peer_id
        )

        for k, v in self._storage.items():
            setattr(new_env, k, v)

        for k, v in self._replaced_methods.items():
            new_env.replace_method(k, v)

        return new_env

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
