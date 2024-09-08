import asyncio
import logging
from itertools import groupby
from typing import Callable, Dict, List

from .backend import Backend
from .context import Context
from .plugin import Plugin
from .router import ListRouter, Router
from .storage import Storage
from .storages import MemoryStorage

# Find proper methods for different python versions
if hasattr(asyncio.Task, "all_tasks"):
    _all_tasks = asyncio.Task.all_tasks  # type: ignore
else:
    _all_tasks = asyncio.all_tasks

if hasattr(asyncio.Task, "current_task"):
    _current_task = asyncio.Task.current_task  # type: ignore
else:
    _current_task = asyncio.current_task


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
    ):
        self._plugins: List[Plugin] = []
        self._backends: List[Backend] = []
        self._storages: Dict[str, Storage] = {"default": MemoryStorage()}
        self._root_router: Router

        self._hooks: Dict[str, List[Callable]] = {
            "start": [],
            "exception": [],
            "completion": [],
            "shutdown": [],
        }

        self._concurrent_handlers_count = concurrent_handlers_count
        self._semaphore = asyncio.Semaphore(value=concurrent_handlers_count)

        self.config = {
            "prefixes": ("/",),
            "mention_prefixes": ("", ","),
        }

    def _prepare_routers(self):
        source_routers = []

        for plugin in self._plugins:
            source_routers.extend(plugin._routers)

        sorted_source_routers = sorted(
            source_routers, reverse=True, key=lambda router: router.priority
        )

        root_router = ListRouter()

        for _, outer_group in groupby(
            sorted_source_routers, key=lambda router: router.priority
        ):
            for cls, inner_group in groupby(outer_group, key=type):
                if issubclass(cls, Router):
                    root_router.add_handler(cls.merge(inner_group))

        self._root_router = root_router

    async def _handle_event(self, event: str, *args, **kwargs):
        for handler in self._hooks[event]:
            try:
                await handler(*args, **kwargs)
            except Exception:
                logging.exception('Error while handling event "%s"', event)

    def add_storage(self, name, storage):
        """Add storage to the application (replaces previous if needed)."""
        if not isinstance(storage, Storage):
            raise ValueError(f"Provided value is not a storage: {storage}")
        self._storages[name] = storage

    @property
    def storages(self):
        return self._storages

    def add_plugin(self, plugin: Plugin):
        """Add plugin to the application."""
        if plugin in self._plugins:
            raise RuntimeError("Plugin already added")

        plugin.app = self
        self._plugins.append(plugin)

        self._prepare_routers()

    @property
    def plugins(self):
        return self._plugins

    def add_backend(self, backend: Backend):
        """Add backend to the application."""
        if backend in self._backends:
            raise RuntimeError("Backend already added")

        self._backends.append(backend)

    @property
    def backends(self):
        return self._backends

    async def _run_wrapper(self):
        try:
            return await self._run()
        except KeyboardInterrupt:
            pass
        except Exception:
            logging.exception("Error while running application:")

    async def _run(self):
        logging.debug("Initiating storages")

        for storage in self._storages.values():
            await storage.init()

        logging.debug("Initiating hooks")
        for plugin in self._plugins:
            for event, handler in plugin._hooks:
                self._hooks[event].append(handler)

        logging.debug("Creating queue for acquired updates")
        queue = asyncio.Queue(maxsize=self._concurrent_handlers_count)

        logging.debug("Preparing backends and starting background updates acquiring")
        for backend in self._backends:
            await backend.on_start(self)
            asyncio.ensure_future(backend.acquire_updates(queue))

        logging.debug("Handling start event")
        await self._handle_event("start")

        logging.debug("Running processing loop")
        try:
            while True:
                await self._semaphore.acquire()

                update, backend = await queue.get()
                context = Context(self, update, backend)
                await backend.setup_context(context)

                task = asyncio.ensure_future(self._handle_update(context))
                task.add_done_callback(lambda _: self._semaphore.release())
        except asyncio.CancelledError:
            raise
        except Exception:
            self.stop()
            raise

    async def _handle_update(self, context: Context):
        logging.debug("Processing update %s", context.update)

        try:
            await self._root_router.handle(context.update, context)
            await self._handle_event("completion", context)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logging.exception("Exception while handling the update")
            await self._handle_event("exception", context, exc)

    async def _shutdown_wrapper(self):
        try:
            return await self._shutdown()
        except Exception:
            logging.exception("Error while shutting down application:")

    async def _shutdown(self):
        logging.info("Gracecfully shutting application down...")

        # Cancel everything
        tasks = []

        for task in _all_tasks():
            if task is not _current_task():
                task.cancel()
                tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        # Clean up
        tasks = []

        for backend in self._backends:
            tasks.append(backend.on_shutdown(self))

        tasks.append(self._handle_event("shutdown"))

        await asyncio.gather(*tasks, return_exceptions=True)

        # Stop loop
        asyncio.get_event_loop().stop()

    def run(self):
        """Run the application."""
        logging.info("Starting application...")

        try:
            asyncio.ensure_future(self._run_wrapper())
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            asyncio.ensure_future(self._shutdown_wrapper())
            asyncio.get_event_loop().run_forever()
        finally:
            asyncio.get_event_loop().close()
            logging.info("Stopped application")

    def stop(self):
        """Stop the application."""
        return asyncio.ensure_future(self._shutdown_wrapper())
