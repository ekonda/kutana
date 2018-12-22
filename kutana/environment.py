class Environment:
    __slots__ = (
        "_has_message", "_message", "meta",
        "manager", "parent_environment",
    )

    def __init__(self, manager, parent_environment=None):
        self.manager = manager
        self.parent_environment = parent_environment

        self._has_message = None
        self._message = None

        self.meta = {}

    @property
    def manager_type(self):
        return self.manager.type

    def spawn(self):
        return self.__class__(self.manager, self)

    def has_message(self):
        return self._has_message

    def get_message(self):
        return self._message

    def set_message(self, message):
        """
        Change message that will be passed to every sequential callbacks'
        calls. Message should be instance of :class:`.Message`
        """

        self._message = message
        self._has_message = message is not None

    async def convert_to_message(self, update):
        """
        Create and return :class:`Message` object from passed `update` object.
        Return None if :class:`.Message` can't be created.
        """

        raise NotImplementedError

    async def reply(self, message):
        """
        Reply with specified text to message currently being processed. Return
        None if environment wasn't able to determine message's recipient.
        """

        raise NotImplementedError

    async def send_message(self, message, peer_id):
        """Send specified text to user with specified id."""

        raise NotImplementedError
