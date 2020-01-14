from collections import namedtuple
from enum import Enum


class UpdateType(Enum):
    MSG = 1
    UPD = 2


Update = namedtuple("Update", ("raw", "type"))


class ReceiverType(Enum):
    SOLO = 1
    MULTI = 2
    UNKNOWN = 3


Message = namedtuple("Message", (
    "raw", "type", "text", "attachments", "sender_id",
    "receiver_id", "receiver_type", "date",
))


ATTACHMENT_TYPES = (
    "image", "doc", "sticker", "video", "audio", "voice"
)


AttachmentData = namedtuple("AttachmentData", (
    "id", "type", "title", "file", "file_name", "file_getter",
    "raw",
))


class Attachment(AttachmentData):
    __slots__ = ()

    @classmethod
    def new(
        cls, file, file_name="image.png", type="image", title=""
    ):
        """
        Create a new attachment with provided type, file (contents) and
        file_name. Also accepts title.

        :rtype: kutana.update.Attachment
        """

        return Attachment(
            None,
            type,
            title,
            file,
            file_name,
            None,
            None,
        )

    @classmethod
    def existing(cls, id, type):
        """
        Create an attachment that was already uploaded and you have it's ID
        and type.

        :rtype: kutana.update.Attachment
        """

        return Attachment(
            id,
            type,
            None,
            None,
            None,
            None,
            "missing",
        )

    @classmethod
    def _existing_full(
        cls, id, type, title, file_name, getter, raw,
    ):
        """
        This method is used internally for creating attachments
        with concrete data.

        :rtype: kutana.update.Attachment
        """

        return Attachment(
            id,
            type,
            title,
            None,
            file_name,
            getter,
            raw,
        )

    @property
    def uploaded(self):
        return self.raw is not None

    async def get_file(self):
        """
        Download file stored in attachments if available. Raises
        ValueError if contents can't be downloaded.

        :rtype: kutana.update.Attachment
        """

        if self.file is not None:
            return self.file

        if self.file_getter is not None:
            return await self.file_getter()

        raise ValueError("No way to get file from attachment")
