from kutana.exceptions import ExitException
from kutana.executor import Executor
import asyncio


class Kutana:
    """Main class for constructing engine."""

    def __init__(self, executor=None, loop=None):
        self.managers = []
        self.executor = executor or Executor()

        self.loop = loop or asyncio.get_event_loop()

        self.storage = {}

        self.running = True
        self.loops = []
        self.tasks = []
        self.prcss = []

        self.gathered_loops = None

    def add_manager(self, manager):
        """Add manager to engine."""

        self.managers.append(manager)

    async def process_update(self, mngr, update):
        """Prepare environment and process update from manager."""

        eenv = {
            "mngr_type": mngr.type,
            "convert_to_message": mngr.convert_to_message
        }

        await mngr.setup_env(update, eenv)

        await self.executor(update, eenv)

    def ensure_future(self, awaitable):
        """Shurtcut for asyncio.ensure_loop with active loop."""

        future = asyncio.ensure_future(awaitable, loop=self.loop)

        self.prcss.append(future)

        return future

    async def loop_for_manager(self, mngr):
        """Receive and process updates from target manager."""

        receiver = await mngr.get_receiver_coroutine_function()

        while self.running:
            for update in await receiver():
                self.ensure_future(
                    self.process_update(
                        mngr, update
                    )
                )

            await asyncio.sleep(0.01)

    def run(self):
        """Start engine."""

        asyncio.set_event_loop(self.loop)

        self.loops = []

        for manager in self.managers:
            self.loops.append(self.loop_for_manager(manager))

            awaitables = self.loop.run_until_complete(
                manager.get_background_coroutines(self.ensure_future)
            )

            for awaitable in awaitables:
                self.loops.append(awaitable)

        self.loop.run_until_complete(
            self.executor(
                {
                    "kutana": self, "update_type": "startup",
                    "registered_plugins": self.executor.registered_plugins
                },
                {
                    "mngr_type": "kutana"
                }
            )
        )

        try:
            self.gathered = asyncio.gather(*self.loops, *self.tasks)

            self.loop.run_until_complete(self.gathered)
        except (KeyboardInterrupt, ExitException):
            pass

        finally:
            self.running = False

        self.loop.run_until_complete(self.dispose())

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        await asyncio.gather(*self.prcss)

        await self.executor.dispose()

        for manager in self.managers:
            await manager.dispose()
