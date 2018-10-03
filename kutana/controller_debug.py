from kutana.controller_basic import BasicController
from kutana.plugin import Message
from kutana.exceptions import ExitException


class DebugController(BasicController):
    """Shoots target texts once."""

    type = "debug"

    def __init__(self, *texts):
        self.replies = []
        self.replies_others = {}

        self.queue = list(texts)
        self.dead = False

    async def upload_thing(self, thing, **kwargs):
        return thing

    async def make_reply(self, update):
        async def reply(message, attachment=None, **kwargs):
            if isinstance(update, (list, tuple)) and len(update) == 2:
                peer_id = update[0]

            else:
                peer_id = 1

            await self.send_message(message, peer_id=peer_id, attachment=attachment)

        return reply

    async def send_message(self, message, peer_id=None, attachment=None,
            **kwargs):
        if peer_id and peer_id != 1:
            if peer_id in self.replies_others:
                t = self.replies_others[peer_id]

            else:
                t = []
                self.replies_others[peer_id] = t

        else:
            t = self.replies

        if message:
            t.append(message)

        if attachment:
            if not isinstance(attachment, (list, tuple)):
                attachment = [attachment]

            for at in attachment:
                t.append(at)

    async def setup_env(self, update, eenv):
        async def return_none(*args, **kwargs):
            return None

        eenv["reply"] = await self.make_reply(update)
        eenv["send_message"] = self.send_message

        eenv["upload_doc"] = self.upload_thing
        eenv["upload_photo"] = self.upload_thing

        eenv["request"] = return_none

    @staticmethod
    async def convert_to_message(update, eenv):
        if isinstance(update, (list, tuple)) and len(update) == 2:
            return Message(
                update[1], (), update[0], update[0], update
            )

        return Message(
            str(update), (), 1, 1, (1, str(update))
        )

    async def get_background_coroutines(self, ensure_future):
        return []

    async def get_receiver_coroutine_function(self):
        async def rec():
            if self.dead:
                raise ExitException

            self.dead = True

            return self.queue

        return rec

    async def dispose(self):
        pass
