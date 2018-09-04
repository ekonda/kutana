from kutana.controllers.basic import BasicController
from kutana.plugindata import Message
from kutana.exceptions import ExitException


class DumpingController(BasicController):
    """Shoots target texts once."""

    type = "dumping"

    def __init__(self, *texts):
        self.die = False
        self.queue = list(texts)

    async def async_print(self, *args, **kwargs):
        print(*args, **kwargs)

    async def setup_env(self, update, eenv):
        eenv["reply"] = self.async_print

    @staticmethod
    async def convert_to_message(update, eenv):
        return Message(
            update, (), "U", "KU", update
        )

    async def get_background_coroutines(self, ensure_future):
        return []

    async def get_receiver_coroutine_function(self):
        async def rec():
            if self.die:
                raise ExitException

            self.die = True

            return self.queue

        return rec

    async def dispose(self):
        pass
