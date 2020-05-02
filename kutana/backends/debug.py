from types import GeneratorType
from ..backend import Backend
from ..update import Message, ReceiverType, UpdateType


class Debug(Backend):
    def __init__(self, messages=None, on_complete=None, save_replies=True):
        if isinstance(messages, GeneratorType):  # pragma: no cover
            self.messages = messages
            self.messages_count = -1
        else:
            self.messages = (m for m in messages)
            self.messages_count = len(messages)

        self.save_replies = save_replies
        self.answers = {}
        self.answers_count = 0

        self.responses = []

        self.on_complete = on_complete

    def _make_update(self, data):
        return Message(
            raw=None,
            type=UpdateType.MSG,
            text=data[0],
            attachments=(),
            sender_id=data[1],
            receiver_id=0,
            receiver_type=ReceiverType.SOLO,
            date=0,
        )

    async def perform_updates_request(self, submit_update):
        if not self.messages:
            return

        for _ in range(25):
            try:
                await submit_update(self._make_update(next(self.messages)))
            except StopIteration:
                self.messages = None
                break

    async def perform_send(self, target_id, message, attachments, kwargs):
        if self.save_replies:
            if target_id not in self.answers:
                self.answers[target_id] = []

            self.answers[target_id].append(
                (message, attachments, kwargs)
            )

        self.answers_count += 1

        if self.answers_count == self.messages_count and self.on_complete:
            self.on_complete()
