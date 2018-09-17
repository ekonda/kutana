from kutana.controller_basic import BasicController
from kutana.plugin import Message
from kutana.exceptions import ExitException


class DebugController(BasicController):
    """Shoots target texts once."""

    type = "debug"

    def __init__(self, *texts):
        self.replies = []

        self.queue = list(texts)
        self.dead = False

    async def upload_thing(self, thing, **kwargs):
        return thing

    async def reply(self, message, attachment=None):
        if message:
            self.replies.append(message)

        if attachment:
            if isinstance(attachment, (list, tuple)):
                for a in attachment:
                    self.replies.append(a)

            else:
                self.replies.append(attachment)

    async def setup_env(self, update, eenv):
        eenv["reply"] = self.reply

        eenv["upload_doc"] = self.upload_thing
        eenv["upload_photo"] = self.upload_thing

    @staticmethod
    async def convert_to_message(update, eenv):
        return Message(
            update, (), "U", "KU", update
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
