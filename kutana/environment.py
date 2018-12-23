"""Base environment for manager."""

class Environment:
    """Base environment for manager."""

    __slots__ = (
        "_has_message", "_message", "meta",
        "manager", "parent_environment", "peer_id"
    )

    def __init__(self, manager, parent_environment=None, peer_id=None):
        self.manager = manager
        self.parent_environment = parent_environment

        self.peer_id = peer_id

        self._has_message = None
        self._message = None

        self.meta = {}

    @property
    def manager_type(self):
        """Return currently processed message's manager type."""

        return self.manager.type

    def spawn(self):
        """
        Create partial copy of environment with this environment as parent.
        Environment's `meta` is not copied.
        """

        return self.__class__(self.manager, self)

    def has_message(self):
        """
        Return True if message was converted from update
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
