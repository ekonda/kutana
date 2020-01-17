import sys
import time
import select
from ..backend import Backend
from ..update import Message, ReceiverType, UpdateType


class Terminal(Backend):
    def _make_update(self, text, sender_id=1):
        return Message(
            raw=None,
            type=UpdateType.MSG,
            text=text,
            attachments=(),
            sender_id=sender_id,
            receiver_id=1,
            receiver_type=ReceiverType.SOLO,
            date=time.time(),
        )

    async def perform_updates_request(self, submit_update):
        ready_objects, _, _ = select.select([sys.stdin], [], [], 0.1)

        if ready_objects:
            message = sys.stdin.readline().strip()
            await submit_update(self._make_update(message))

    async def perform_send(self, target_id, message, attachments, kwargs):
        print(">", message)
