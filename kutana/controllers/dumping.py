from kutana.controllers.basic import BasicController
from kutana.plugindata import Message
from kutana.exceptions import ExitException


class DumpingController(BasicController):
    """Shoots target texts once."""

    type = "dumping"

    def __init__(self, *texts):
        self.replies = []
        self.queue = list(texts)
        self.dead = False

    async def reply(self, msg, print_msg=False):
        self.replies.append(msg)

        if print_msg:
            print(msg)

    async def setup_env(self, update, eenv):
        eenv["reply"] = self.reply

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
