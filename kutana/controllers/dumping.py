from kutana.controllers.basiccontroller import BasicController
from kutana.exceptions import ExitException


class DumpingController(BasicController):
    """Shoots target texts once."""

    TYPE = "dumping"

    def __init__(self, *texts):
        self.die = False
        self.queue = list(texts)

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
