from kutana.executor import Executor
from kutana.exceptions import ExitException
from kutana.tools.structures import objdict
import asyncio


class Kutana:
    """Main class for constructing engine."""

    def __init__(self, executor=None, loop=None):
        self.controllers = []
        self.executor = executor or Executor()

        self.loop = loop or asyncio.get_event_loop()

        self.running = True
        self.loops = []
        self.tasks = []
        self.gathered_loops = None

        self.settings = objdict()

    def add_controller(self, controller):
        """Adding controller to engine."""

        self.controllers.append(controller)

    def apply_environment(self, environment):
        """Shortcut for adding controller and updating executor."""

        self.add_controller(environment["controller"])
        self.executor.add_callbacks_from(environment["executor"])

    async def shedule_update_process(self, controller_type, update):
        """Shedule update to be processed."""

        await self.ensure_future(self.executor(controller_type, update))

    async def ensure_future(self, awaitable):
        """Shurtcut for asyncio.ensure_loop with curretn loop."""

        await asyncio.ensure_future(awaitable, loop=self.loop)

    async def loop_for_controller(self, controller):
        """Receive and process updated from target controller."""

        receiver = await controller.create_receiver()

        while self.running:
            for update in await receiver():
                await self.shedule_update_process(controller.TYPE, update)

            await asyncio.sleep(0.05)

    def run(self):
        """Start engine."""

        asyncio.set_event_loop(self.loop)

        self.loops = []

        for controller in self.controllers:
            self.loops.append(self.loop_for_controller(controller))

            awaitables = self.loop.run_until_complete(
                controller.create_tasks(self.ensure_future)
            )

            for awaitable in awaitables:
                self.loops.append(awaitable())

        self.loop.run_until_complete(self.shedule_update_process(
            "kutana",
            {
                "kutana": self, "update_type": "startup",
                "callbacks_owners": self.executor.callbacks_owners
            }
        ))

        try:
            self.gathered = asyncio.gather(*self.loops, *self.tasks)

            self.loop.run_until_complete(self.gathered)
        except (KeyboardInterrupt, ExitException):
            pass

        self.loop.run_until_complete(self.dispose())

    async def dispose(self):
        """Free resourses and prepare for shutdown."""

        await self.executor.dispose()

        for controller in self.controllers:
            await controller.dispose()
