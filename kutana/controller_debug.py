from kutana.controller_basic import BasicController
from kutana.plugin import Message
from kutana.exceptions import ExitException


class DebugController(BasicController):
    """Shoots target texts once."""

    type = "debug"

    def __init__(self, *texts):
        self.replies = []
        self.replies_all = {}

        self.queue = list(texts)
        self.dead = False

    async def upload_thing(self, thing, **kwargs):
        return thing

    async def make_reply(self, update):
        if isinstance(update, str):
            sender_id = 1

        else:
            sender_id = update[0]

        async def reply(message, attachment=None, **kwargs):
            await self.send_message(
                message, peer_id=sender_id, attachment=attachment
            )

        return reply

    async def send_message(self, message=None, peer_id=None, attachment=None,
            **kwargs):

        sender_id = peer_id if peer_id is not None else 1

        array = self.replies_all.get(sender_id, [])

        if message:
            array.append(message)

            if sender_id == 1:
                self.replies.append(message)

        if attachment:
            if not isinstance(attachment, (list, tuple)):
                attachment = [attachment]

            array += attachment

            if sender_id == 1:
                self.replies += attachment

        else:
            attachment = []

        self.replies_all[sender_id] = array

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
        # update = (sender_id, message)
        # or
        # update = (message_from_user_with_id_1)

        if isinstance(update, str):
            return Message(
                str(update), (), 1, 1, (1, str(update))
            )

        return Message(
            update[1], (), update[0], update[0], update
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
