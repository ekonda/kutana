"""Core class for engine."""

import asyncio

from .exceptions import ExitException
from .logger import logger
from .utils import sort_callbacks


class Kutana:

    """
    Main class for constructing application.

    :param loop: loop for working
    """

    def __init__(self, loop=None):
        self.running = True  #: True if application is running
        self.config = {}  #: user's configuration

        self.registered_plugins = []  #: plugins registered in application

        self._callbacks = []
        self._startup_callbacks = []
        self._dispose_callbacks = []

        self._managers = []
        self._loop = loop or asyncio.get_event_loop()
        self._tasks = []
        self._tasks_loops = []

    def register_startup(self, *callbacks, priority=0):
        """
        Register callbacks for startup.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        """

        for callback in callbacks:
            self._startup_callbacks.append((priority, callback))

        sort_callbacks(self._startup_callbacks)

    def register_dispose(self, *callbacks, priority=0):
        """
        Register callbacks for disposing resourses before shutting down.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        """

        for callback in callbacks:
            self._dispose_callbacks.append((priority, callback))

        sort_callbacks(self._dispose_callbacks)

    def register(self, *callbacks, priority=0):
        """
        Register callbacks for processing updates with specified priority.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        """

        for callback in callbacks:
            self._callbacks.append((priority, callback))

        sort_callbacks(self._callbacks)

    def register_plugins(self, plugins):
        """
        Register plugins in application.

        :param plguins: plugins for registration
        """

        for plugin in plugins:
            self.register(
                *plugin.get_callbacks(), priority=plugin.priority
            )

            self.register_startup(
                *plugin.get_callbacks_for_startup(), priority=plugin.priority
            )

            self.register_dispose(
                *plugin.get_callbacks_for_dispose(), priority=plugin.priority
            )

            self.registered_plugins.append(plugin)

    def add_manager(self, manager):
        """Add manager to application."""

        self._managers.append(manager)

    async def process(self, mngr, update):
        """Create environment and process update from manager."""

        env = await mngr.get_environment(update)

        try:
            await env.process(update, self._callbacks)

        except Exception as e:  # pylint: disable=W0703
            await env.reply(
                "Произошла крайне критическая ошибка. Сообщите об этом "
                "администратору."
            )

            logger.exception(e)

    async def loop_for_manager(self, mngr):
        """Receive and process updates from target manager forever."""

        receiver = await mngr.get_receiver_coroutine_function()

        while self.running:
            for update in await receiver():
                task = asyncio.ensure_future(
                    self.process(mngr, update), loop=self._loop
                )

                self._tasks.append(task)

            await asyncio.sleep(0)

    def run(self):
        """Start application."""

        asyncio.set_event_loop(self._loop)

        for manager in self._managers:
            self._tasks_loops.append(self.loop_for_manager(manager))

            self._loop.run_until_complete(
                manager.startup(self)
            )

            # awaitables = self._loop.run_until_complete(
            #     manager.startup(self.ensure_future)
            # )

            # for awaitable in awaitables:
            #     self._tasks_loops.append(awaitable)

        self._loop.run_until_complete(self.startup())

        try:
            self._loop.run_until_complete(asyncio.gather(*self._tasks_loops))

        except (KeyboardInterrupt, ExitException):
            pass

        finally:
            self.running = False

        self._loop.run_until_complete(self.dispose())

    async def startup(self):
        """Prepare plugins for work."""

        for _, callback in self._startup_callbacks:
            await callback(self)


    async def dispose(self):
        """Free resources and prepare for shutdown."""

        await asyncio.gather(*self._tasks)

        for _, callback in self._dispose_callbacks:
            await callback()

        for manager in self._managers:
            await manager.dispose()
