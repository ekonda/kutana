"""Manager and environment for debug purposes."""

import time
from kutana.manager.basic import BasicManager
from kutana.plugin import Message
from kutana.exceptions import ExitException
from kutana.environment import Environment


class DebugEnvironment(Environment):
    """Environment for :class:`.DebugManager`."""

    def spawn(self):
        return self.__class__(self.manager, self, peer_id=self.peer_id)

    async def reply(self, message, attachment=None):
        """
        Send message to current message's sender.
        See :func:`DebugEnvironment.send_message` for details.
        """

        await self.send_message(
            message, peer_id=self.peer_id, attachment=attachment
        )

    async def send_message(self, *args, **kwargs):
        """Proxy for manager's :func:`DebugManager.send_message` method."""

        await self.manager.send_message(*args, **kwargs)

    async def upload_doc(self, thing, **__):
        """Return first argument."""

        return thing

    async def upload_photo(self, thing, **__):
        """Return first argument."""

        return thing

    async def request(self, *_, **__):
        """Do nothing."""

        return None


class DebugManager(BasicManager):
    """Shoots target texts once and contains replied data."""

    type = "debug"

    def __init__(self, *texts):
        self.replies = []
        self.replies_all = {}

        self.queue = list(texts)
        self.dead = False

    @staticmethod
    async def convert_to_message(update):
        # update = (sender_id, message)
        # or
        # update = (message_from_user_with_id_1)

        if not update:
            return None

        if isinstance(update, str):
            return Message(
                str(update), (), 1, 1, time.time(), (1, str(update))
            )

        return Message(
            update[1], (), update[0], update[0], time.time(), update
        )

    async def send_message(self, message=None, peer_id=None, attachment=None):
        """
        Send message to specified user or user with id 1.

        :param message: message to send
        :param peer_id: recipient's id
        :param attachmnet: optional attachment or list of attachments to
            reply with
        :rtype: None
        """

        peer_id = peer_id if peer_id is not None else 1

        if peer_id not in self.replies_all:
            self.replies_all[peer_id] = []

        replies_all = self.replies_all[peer_id]

        if message:
            replies_all.append(message)

            if peer_id == 1:
                self.replies.append(message)

        if attachment:
            if not isinstance(attachment, (list, tuple)):
                attachment = [attachment]

            replies_all.extend(attachment)

            if peer_id == 1:
                self.replies.extend(attachment)

    async def get_environment(self, update):
        peer_id = update[0] if isinstance(update, (list, tuple)) else 1

        return DebugEnvironment(self, peer_id=peer_id)

    async def get_background_coroutines(self, ensure_future):
        return []

    async def get_receiver_coroutine_function(self):
        async def rec():
            if self.dead:
                raise ExitException

            self.dead = True

            return self.queue

        return rec

    async def dispose(self):
        pass
