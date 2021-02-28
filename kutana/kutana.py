import asyncio
from sortedcontainers import SortedList
from .handler import HandlerResponse as hr
from .storages import MemoryStorage
from .storage import OptimisticLockException, Storage
from .backend import Backend
from .context import Context
from .plugin import Plugin
from .logger import logger


class Kutana:
    """
    Main class for kutana application

    Configuration:

    - '.prefixes' - prefixes for commands (default is [".", "/"])
    - '.ignore_initial_spaces' - ignore spaces after prefix (default is True)

    :ivar ~.config: Application's configuration
    """

    def __init__(
        self,
        concurrent_handlers_count=512,
        default_storage=None,
        loop=None,
    ):
        self._plugins = []
        self._backends = []
        self._storages = {"default": default_storage or MemoryStorage()}

        self._loop = loop or asyncio.new_event_loop()

        self._concurrent_handlers_count = concurrent_handlers_count
        self._sem = asyncio.Semaphore(
            value=concurrent_handlers_count, loop=self._loop
        )

        self._routers = None
        self._handlers = None

        self.config = {
            "prefixes": (".", "/"),
            "ignore_initial_spaces": True
        }

    def get_loop(self):
        """Return application's asyncio loop."""
        # TODO: Replace with property
        return self._loop

    def set_storage(self, name, storage):
        if not isinstance(storage, Storage):
            raise ValueError(f"Provided value is not a storage: {storage}")
        self._storages[name] = storage

    def get_storage(self, name="default"):
        return self._storages.get(name)

    def add_plugin(self, plugin):
        """Add plugin to the application."""
        if not isinstance(plugin, Plugin):
            raise ValueError(f"Provided value is not a plugin: {plugin}")
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
        if not isinstance(backend, Backend):
            raise ValueError(f"Provided value is not a backend: {backend}")
        if backend in self._backends:
            raise RuntimeError("Backend already added")
        self._backends.append(backend)

    def get_backend(self, name):
        """Return first backend with specified name or None."""
        for backend in self._backends:
            if backend.name == name:
                return backend
        return None

    def get_backends(self):
        return self._backends

    async def _on_start(self, queue):
        for storage in self._storages.values():
            await storage.init()

        # Prepare backends and run background update acquiring
        for backend in self._backends:
            await backend.on_start(self)

            if not backend.active:
                continue

            async def acquire_updates(backend):  # don't forget to capture backend
                async def submit_update(update):
                    return await queue.put((update, backend))

                while True:
                    if queue.qsize() < queue.maxsize:
                        await backend.acquire_updates(submit_update)
                    await asyncio.sleep(0)

            asyncio.ensure_future(acquire_updates(backend), loop=self._loop)

        # Prepare plugins
        for plugin in self._plugins:
            plugin.app = self

        # Run event listeners
        await self._handle_event("start")

    async def _main_loop_wrapper(self):
        try:
            await self._main_loop()
        except asyncio.CancelledError:
            pass
        except Exception:
            self.stop()
            raise

    async def _main_loop(self):
        queue = asyncio.Queue(
            maxsize=self._concurrent_handlers_count,
            loop=self._loop
        )

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

    def _init_handlers(self):
        self._handlers = {}

        for event in ["start", "before", "after", "exception", "shutdown"]:
            self._handlers[event] = SortedList([], key=lambda r: -r.priority)

        for plugin in self._plugins:
            for event, handlers in plugin._handlers.items():
                self._handlers[event].update(handlers)

    async def _handle_event(self, name, *args, **kwargs):
        if self._handlers is None:
            self._init_handlers()

        for handler in self._handlers.get(name):
            await handler.handle(*args, **kwargs)

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
        except OptimisticLockException as exc:
            logger.debug("Optimistic lock exception: %s", exc)
        except Exception as exc:
            logger.exception("Exception while handling the update")
            await self._handle_event("exception", update, ctx, exc)

    async def _handle_update(self, update, ctx):
        if self._routers is None:
            self._init_routers()

        await self._handle_event("before", update, ctx)

        for router in self._routers:
            if await router.handle(update, ctx) != hr.SKIPPED:
                ctx._result = hr.COMPLETE
                break
        else:
            ctx._result = hr.SKIPPED

        await self._handle_event("after", update, ctx, ctx._result)

        return ctx._result

    async def _shutdown(self):
        logger.info("Gracecfully shutting application down...")

        # Clean up
        tasks = []

        for backend in self._backends:
            tasks.append(backend.on_shutdown(self))

        tasks.append(self._handle_event("shutdown"))

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
        """Run the application."""
        logger.info("Starting application...")

        try:
            asyncio.ensure_future(self._main_loop_wrapper(), loop=self._loop)
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
