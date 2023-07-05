import io
from enum import Enum
from typing import Any, Awaitable, Callable, List, NamedTuple, Optional, Union, Tuple


class AttachmentKind(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"


class AttachmentContent(NamedTuple):
    name: str
    value: Union[io.IOBase, bytes]


class Attachment:
    def __init__(
        self,
        id: Optional[Union[str, int, float]] = None,
        kind: Optional[Union[AttachmentKind, str]] = None,
        content: Optional[Union[AttachmentContent, Tuple[str, Union[str, bytes]]]] = None,
        title: Optional[str] = None,
        raw: Any = None,
        get_file: Optional[Callable[..., Awaitable]] = None,
    ):
        if not id and not content:
            raise ValueError("Attachment at least should have id or content")

        self.id = id
        self.kind = kind
        self.content = content  # named tuple of (name of content, content)
        self.title = title  # human-friendly description of attachment
        self.raw: Any = raw
        self._get_file = get_file
        self._file = None

    async def get_content(self):
        if self._file is not None:
            return self._file

        if self._get_file is None:
            raise ValueError("Can't get content for this file")

        file = await self._get_file()
        self._file = file
        return file


class RecipientKind(str, Enum):
    GROUP_CHAT = "group_chat"
    PRIVATE_CHAT = "private_chat"


class Message:
    def __init__(
        self,
        sender_id: str,
        recipient_id: str,
        recipient_kind: RecipientKind,
        text: str,
        attachments: List[Attachment],
        date: int,
        raw: Any,
    ):
        self.sender_id: str = sender_id
        self.recipient_id: str = recipient_id
        self.recipient_kind: RecipientKind = recipient_kind
        self.text: str = text
        self.attachments: List[Attachment] = attachments
        self.date: int = date
        self.raw: Any = raw
