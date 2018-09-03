from kutana.controllers.basiccontroller import BasicController
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

    async def create_tasks(self, ensure_future):
        return []

    async def create_receiver(self):
        async def rec():
            if self.die:
                raise ExitException

            self.die = True

            return self.queue

        return rec

    async def dispose(self):
        pass
