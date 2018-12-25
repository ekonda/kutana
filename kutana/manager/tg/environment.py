"""Environment for :class:`.TGManager`."""

from collections import namedtuple

from kutana.environment import Environment


TGAttachmentTemp = namedtuple(
    "TGAttachmentTemp",
    "type content"
)


TGAttachmentTemp.__doc__ = """
Tricky namedtuple for storing not yet uploaded files.
"""


class TGEnvironment(Environment):
    """Environment for :class:`.TGManager`"""

    async def request(self, method, **kwargs):
        """Proxy for manager's `request` method."""

        return await self.manager.request(method, **kwargs)

    async def send_message(self, message, peer_id, attachment=None):
        """Proxy for manager's `send_message` method."""

        return await self.manager.send_message(
            message,
            peer_id,
            attachment
        )

    async def reply(self, message, attachment=None):
        """
        Reply to currently processed message. If text is too long - message
        will be splitted into parts.

        :param message: message to reply with
        :param attachmnet: optional attachment or list of attachments to
            reply with
        :param sticker_id: id of sticker to reply with
        :param payload: json data to reply with (see vk.com/dev for details)
        :param keyboard: json formatted keyboard to reply with (see
            vk.com/dev for details)
        :param forward_messages: messages's id to forward with reply
        :rtype: list with results of sending messages
        """

        if self.peer_id is None:
            return ()

        if len(message) < 4096:
            return (
                await self.manager.send_message(
                    message, self.peer_id, attachment
                ),
            )

        result = []  # TODO: Move splitting to Manager

        chunks = list(
            message[i : i + 4096] for i in range(0, len(message), 4096)
        )

        for chunk in chunks[:-1]:
            result.append(
                await self.manager.send_message(chunk, self.peer_id)
            )

        result.append(
            await self.manager.send_message(
                chunks[-1], self.peer_id, attachment
            )
        )

        return result

    async def upload_doc(self, file):
        """
        Pack file to be sent with :func:`.send_message`
        (or :func:`.reply`).
        """

        return TGAttachmentTemp("document", file)

    async def upload_photo(self, file):
        """
        Pack photo to be sent with :func:`.send_message`
        (or :func:`.reply`).
        """

        return TGAttachmentTemp("photo", file)
