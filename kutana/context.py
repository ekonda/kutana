from typing import Union

from .helpers import chunks
from .update import Message


class Context:
    def __init__(self, app, update, backend):
        self.app = app
        self.update: Union[Message, dict] = update
        self.backend = backend

    def __getattr__(self, name):
        """Defined for typing"""
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """Defined for typing"""
        return super().__setattr__(name, value)

    @property
    def sender_unique_id(self):
        if isinstance(self.update, Message):
            sender_id = self.update.sender_id
        elif hasattr(self, "sender_id"):
            sender_id = self.sender_id
        else:
            raise ValueError("Can't form an unique sender id")

        return f"{self.backend.get_identity()}:s:{sender_id}"

    @property
    def recipient_unique_id(self):
        if isinstance(self.update, Message):
            recipient_id = self.update.recipient_id
        elif hasattr(self, "recipient_id"):
            recipient_id = self.recipient_id
        else:
            raise ValueError("Can't form an unique recipient id")

        return f"{self.backend.get_identity()}:r:{recipient_id}"

    @property
    def request(self):
        return self.backend.request

    async def send_message(self, recipient_id, text=None, attachments=None, **kwargs):
        results = []

        text_segments = list(chunks(str(text))) if text else [None]

        for text_segment in text_segments[:-1]:
            results.append(await self.backend.send_message(recipient_id, text_segment))

        results.append(
            await self.backend.send_message(
                recipient_id,
                text_segments[-1],
                attachments,
                **kwargs,
            )
        )

        return results

    async def reply(self, text=None, attachments=None, **kwargs):
        if isinstance(self.update, Message):
            recipient_id = self.update.recipient_id
        elif hasattr(self, "recipient_id"):
            recipient_id = self.recipient_id
        else:
            raise ValueError("You can't reply to this update")

        return await self.send_message(
            recipient_id,
            text,
            attachments,
            **kwargs,
        )


def split_large_text(text: str, length=4096):
    """
    Split text into chunks with specified length.

    :param text: text for splitting
    :param length: maximum size for one chunk
    :returns: tuple of chunks
    """

    text = str(text)

    yield text[0:length]

    for i in range(length, len(text), length):
        yield text[i : i + length]
