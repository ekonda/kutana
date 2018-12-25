"""Environment for :class:`.TGManager`."""

from collections import namedtuple

from kutana.environment import Environment


TGAttachmentTemp = namedtuple(
    "TGAttachmentTemp",
    "type content kwargs"
)


TGAttachmentTemp.__doc__ = """
Tricky namedtuple for storing not yet uploaded files.
"""


class TGEnvironment(Environment):
    """Environment for :class:`.TGManager`"""

    async def request(self, method, **kwargs):
        """Proxy for manager's "request" method."""

        return await self.manager.request(method, **kwargs)

    async def send_message(self, message, peer_id, attachment=None):
        """Proxy for manager's "send_message" method."""

        return await self.manager.send_message(
            message, peer_id, attachment
        )

    async def reply(self, message, attachment=None, **kwargs):
        """
        Reply to currently processed message. If text is too long - message
        will be splitted into parts.

        :param message: message to reply with
        :param attachment: optional attachment or list of attachments to
            reply with
        :param kwargs:
        :rtype: list with results of sending messages
        """

        return await self.send_message(
            message, self.peer_id, attachment=attachment, **kwargs
        )

    async def upload_doc(self, file, **kwargs):
        """
        Pack file to be sent with :func:`.send_message`
        (or :func:`.reply`) as document.

        :param file: photo as file or bytes
        :param kwargs: arguments for telegram's "sendFile"
        :rtype: :class:`.TGAttachmentTemp`
        """

        return TGAttachmentTemp("document", file, kwargs)

    async def upload_photo(self, file, **kwargs):
        """
        Pack file to be sent with :func:`.send_message`
        (or :func:`.reply`) as photo.

        :param file: photo as file or bytes
        :param kwargs: arguments for telegram's "sendPhoto"
        :rtype: :class:`.TGAttachmentTemp`
        """

        return TGAttachmentTemp("photo", file, kwargs)

    async def get_file_from_attachment(self, attachment):
        """
        Try to download attachment with specified path and return it as bytes.

        :param attachment: :class:`.Attachment`
        :rtype: bytes or None
        """

        file_data = await self.manager.request(
            "getFile", file_id=attachment.id
        )

        if file_data.error:
            return None

        return await self.manager.request_file(file_data.response["file_path"])
