import asyncio
from sortedcontainers import SortedList
from .handler import HandlerResponse as hr
from .storages import NaiveMemory
from .context import Context
from .logger import logger


class Kutana:
    """
    Main class for kutana application

    :ivar ~.storage: Storage for things like states, e.t.c.
    :ivar ~.config: Application's configuration
    """

    def __init__(
        self,
        concurrent_handlers_count=3000,
        storage=None,
        loop=None,
    ):
        self._plugins = []
        self._backends = []

        self._loop = loop or asyncio.new_event_loop()

        self._sem = asyncio.Semaphore(
            value=concurrent_handlers_count, loop=self._loop
        )

        self._routers = None

        self.storage = storage

        self.config = {
            "prefixes": (".", "/"),
        }

    def get_loop(self):
        """Return application's asyncio loop."""
        return self._loop

    def add_plugin(self, plugin):
        """Add plugin to the application."""
        if plugin in self._plugins:
            raise RuntimeError("Plugin already added")
        self._plugins.append(plugin)

    def add_plugins(self, plugins):
        """Add every plugin in passed iterable to the application."""
        for plugin in plugins:
            self.add_plugin(plugin)

    def get_plugins(self):
        """Return list of added plugins."""
        return self._plugins

    def add_backend(self, backend):
        """Add backend to the application."""
        if backend in self._backends:
            raise RuntimeError("Backend already added")
        self._backends.append(backend)

    def get_backends(self):
        return self._backends

    async def _on_start(self, queue):
        for backend in self._backends:
            await backend.on_start(self)

            async def perform_updates_request(backend):
                def submit_update(update):
                    return queue.put((update, backend))

                while True:
                    await backend.perform_updates_request(submit_update)
                    await asyncio.sleep(0)

            asyncio.ensure_future(
                perform_updates_request(backend),
                loop=self._loop
            )

        for plugin in self._plugins:
            if plugin._on_start:
                await plugin._on_start(self)

    async def _main_loop(self):
        if self.storage is None:
            self.storage = NaiveMemory()

        queue = asyncio.Queue(maxsize=32, loop=self._loop)

        await self._on_start(queue)

        while True:
            await self._sem.acquire()

            update, backend = await queue.get()

            ctx = await Context.create(
                app=self,
                config=self.config,
                update=update,
                backend=backend,
            )

            backend.prepare_context(ctx)

            task = asyncio.ensure_future(
                self._handle_update_with_logger(update, ctx),
                loop=self._loop
            )

            task.add_done_callback(lambda t: self._sem.release())

    def _init_routers(self):
        self._routers = SortedList([], key=lambda r: -r.priority)

        def _add_router(new_router):
            for router in self._routers:
                if router.alike(new_router):
                    router.merge(new_router)
                    return

            self._routers.add(new_router)

        for plugin in self._plugins:
            for router in plugin._routers:
                _add_router(router)

    async def _handle_update_with_logger(self, update, ctx):
        logger.debug("Processing update %s", update)

        try:
            return await self._handle_update(update, ctx)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Exception while handling the update")

            for plugin in self._plugins:
                if plugin._on_exception:
                    await plugin._on_exception(update, ctx, exc)

    async def _handle_update(self, update, ctx):
        if self._routers is None:
            self._init_routers()

        for plugin in self._plugins:
            if plugin._on_before:
                await plugin._on_before(update, ctx)

        for router in self._routers:
            if await router.handle(update, ctx) != hr.SKIPPED:
                ctx._result = hr.COMPLETE
                break
        else:
            ctx._result = hr.SKIPPED

        for plugin in self._plugins:
            if plugin._on_after:
                await plugin._on_after(update, ctx, ctx._result)

        return ctx._result

    async def _shutdown(self):
        logger.info("Gracecfully shutting application down...")

        # Clean up
        tasks = []

        for backend in self._backends:
            tasks.append(backend.on_shutdown(self))

        for plugin in self._plugins:
            if plugin._on_shutdown:
                tasks.append(plugin._on_shutdown(self))

        await asyncio.gather(*tasks, loop=self._loop, return_exceptions=True)

        # Cancel everything else
        tasks = []

        for task in asyncio.Task.all_tasks(loop=self._loop):
            if task is not asyncio.Task.current_task():
                task.cancel()
                tasks.append(task)

        await asyncio.gather(*tasks, loop=self._loop, return_exceptions=True)

        self._loop.stop()

    def run(self):
        """Start the application."""
        logger.info("Starting application...")

        try:
            asyncio.ensure_future(self._main_loop(), loop=self._loop)
            self._loop.run_forever()
        except KeyboardInterrupt:
            asyncio.ensure_future(self._shutdown(), loop=self._loop)
            self._loop.run_forever()
        finally:
            self._loop.close()
            logger.info("Stopped application")

    def stop(self):
        """Stop the application."""
        return asyncio.ensure_future(self._shutdown(), loop=self._loop)
