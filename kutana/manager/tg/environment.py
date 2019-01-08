"""Environment for :class:`.TGManager`."""

from collections import namedtuple

from kutana.environment import Environment


TGAttachmentTemp = namedtuple(
    "TGAttachmentTemp",
    "type content kwargs"
)


TGAttachmentTemp.__doc__ = """
Tricky namedtuple for storing not yet uploaded files.

:param type: attachment's type
:param content: attachment's content
:param kwargs: kwargs for telegram's methods
"""


class TGEnvironment(Environment):

    """Environment for :class:`.TGManager`"""

    async def reply(self, message, attachment=None, **kwargs):
        """
        Reply to currently processed message. If text is too long - message
        will be splitted into parts.

        :param message: message to reply with
        :param attachment: optional attachment or list of attachments to
            reply with
        :param kwargs: arguments for telegrams's "sendMessage",
            "sendPhoto" etc.
        :rtype: list with results of sending messages
        """

        return await self.manager.send_message(
            message, self.peer_id, attachment, **kwargs
        )

    async def upload_doc(self, file, **kwargs):
        """
        Pack file to be sent with :func:`.send_message`
        (or :func:`.reply`) as document.

        :param file: document as file or bytes
        :param kwargs: arguments for telegram's "sendFile"
        :rtype: :class:`.TGAttachmentTemp`
        """

        return TGAttachmentTemp("doc", file, kwargs)

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
        file_data = await self.manager.request(
            "getFile", file_id=attachment.id
        )

        if file_data.error:
            return None

        return await self.manager.request_file(
            file_data.response["file_path"]
        )
