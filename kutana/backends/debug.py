from types import GeneratorType
from ..backend import Backend
from ..update import Message, ReceiverType, UpdateType


class Debug(Backend):
    def __init__(self, messages=None, on_complete=None, save_replies=True, **kwargs):
        super().__init__(**kwargs)

        if isinstance(messages, GeneratorType):  # pragma: no cover
            self.messages = messages
        else:
            self.messages = (m for m in messages)

        self.messages_count = 0

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

    async def acquire_updates(self, submit_update):
        if not self.messages:
            return

        for _ in range(25):
            try:
                message = next(self.messages)
                self.messages_count += 1
                await submit_update(self._make_update(message))
            except StopIteration:
                self.messages = None
                break

    async def execute_send(self, target_id, message, attachments, kwargs):
        if self.save_replies:
            if target_id not in self.answers:
                self.answers[target_id] = []

            self.answers[target_id].append(
                (message, attachments, kwargs)
            )

        self.answers_count += 1

        self.check_if_complete()

    def check_if_complete(self):
        if self.messages or not self.on_complete:
            return

        if self.answers_count == self.messages_count:
            self.on_complete()
