from kutana.logger import logger
from kutana.environment import Environment
import sys


class Executor:
    """Class performing callbacks management."""

    def __init__(self):
        self.callbacks = []
        self.error_callbacks = []

        self.startup_callbacks = []
        self.dispose_callbacks = []

        self.registered_plugins = []

    def register_plugins(self, *plugins):
        """Register callbacks from plugins."""

        for plugin in plugins:
            if hasattr(plugin, "_prepare_callbacks"):
                self.register(*plugin._prepare_callbacks())

            if hasattr(plugin, "_prepare_callbacks_error"):
                self.register(*plugin._prepare_callbacks_error(), error=True)

            self.register_startup(*plugin._callbacks_startup)
            self.register_dispose(*plugin._callbacks_dispose)

            self.registered_plugins.append(plugin)

    def register(self, *callbacks, priority=400, error=False):
        """Register callbacks for updates or errors with specified priority."""

        def _register(coroutine):
            callbacks = self.error_callbacks if error else self.callbacks

            callbacks.append(coroutine)

            def get_priority(cb):
                if hasattr(cb, "priority") and cb.priority is not None:
                    return -cb.priority

                return -priority

            callbacks.sort(key=get_priority)

            return coroutine

        for callback in callbacks:
            _register(callback)

        return _register

    def register_startup(self, *callbacks):
        def _register_startup(coroutine):
            self.startup_callbacks.append(coroutine)
            return coroutine

        for callback in callbacks:
            _register_startup(callback)

        return _register_startup

    def register_dispose(self, *callbacks):
        def _register_dispose(coroutine):
            self.dispose_callbacks.append(coroutine)
            return coroutine

        for callback in callbacks:
            _register_dispose(callback)

        return _register_dispose

    async def __call__(self, update, env):
        try:
            for callback in self.callbacks:
                res = await callback(update, env)

                if res == "DONE":
                    break

        except Exception as e:
            logger.exception(
                "\"{}::{}\" on update {} from {}".format(
                    sys.exc_info()[0].__name__, e, update, env.manager_type
                )
            )

            env.meta["exception"] = e

            if not self.error_callbacks:
                return await env.reply(
                    "Произошла ошибка! Приносим свои извинения."
                )

            else:

                for callback in self.error_callbacks:
                    res = await callback(update, env)

                    if res == "DONE":
                        break

    async def startup(self, kutana):
        """Call initialization callbacks."""

        for callback in self.startup_callbacks:
            await callback(kutana, self.registered_plugins)

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        for callback in self.dispose_callbacks:
            await callback()
