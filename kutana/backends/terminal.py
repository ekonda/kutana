import sys
import time
from ..backend import Backend
from ..update import Message, ReceiverType, UpdateType

if sys.platform == "win32":  # pragma: no cover
    import msvcrt

    def attempt_to_read_message():
        if msvcrt.kbhit():
            return sys.stdin.readline().strip()
        return None

else:  # pragma: no cover
    import select

    def attempt_to_read_message():
        ready_objects, _, _ = select.select([sys.stdin], [], [], 0.05)
        return sys.stdin.readline().strip() if ready_objects else None


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

    async def acquire_updates(self, submit_update):
        message = attempt_to_read_message()
        if message:
            await submit_update(self._make_update(message))

    async def execute_send(self, target_id, message, attachments, kwargs):
        print(">", message)
