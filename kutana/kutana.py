"""Core class for engine."""

import asyncio

from kutana.exceptions import ExitException
from kutana.executor import Executor


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

    def add_manager(self, manager):
        """Add manager to engine."""

        self.managers.append(manager)

    async def process_update(self, mngr, update):
        """Create environment and process update from manager."""

        await self.executor.process(update, await mngr.get_environment(update))

    def ensure_future(self, awaitable):
        """
        Schedule awaitable with asyncio.ensure_loop in current loop.
        Add task to list of running tasks.

        :param awaitable: awaitable for scheduling
        :rtype: scheduled task
        """

        task = asyncio.ensure_future(awaitable, loop=self.loop)

        self.tasks.append(task)

        return task

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

            await asyncio.sleep(0)

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

        self.loop.run_until_complete(self.executor.startup(self))

        try:
            self.loop.run_until_complete(
                asyncio.gather(*self.loops)
            )

        except (KeyboardInterrupt, ExitException):
            pass

        finally:
            self.running = False

        self.loop.run_until_complete(self.dispose())

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        await asyncio.gather(*self.tasks)

        await self.executor.dispose()

        for manager in self.managers:
            await manager.dispose()
