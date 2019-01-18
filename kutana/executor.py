"""Class performing callbacks management."""

import sys

from kutana.logger import logger


class Executor:

    """Class performing callbacks management."""

    def __init__(self):
        self.callbacks = []
        self.error_callbacks = []

        self.startup_callbacks = []
        self.dispose_callbacks = []

        self.registered_plugins = []

    def register_plugins(self, plugins):
        """
        Register plugins' callbacks in executor.

        :param plguins: plugins for registration
        """

        for plugin in plugins:
            if hasattr(plugin, "_prepare_callbacks"):
                self.register(*plugin._prepare_callbacks())  # pylint: disable=W0212

            if hasattr(plugin, "_prepare_callbacks_error"):
                self.register(*plugin._prepare_callbacks_error(), error=True)  # pylint: disable=W0212

            self.register_startup(*plugin._callbacks_startup)  # pylint: disable=W0212
            self.register_dispose(*plugin._callbacks_dispose)  # pylint: disable=W0212

            self.registered_plugins.append(plugin)

    def register(self, *callbacks, priority=400, error=False):
        """
        Register callbacks for processing updates or errors with specified
        priority.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        :param error: True if registration for processing errors
        :rtype: decorator for registration
        """

        def _register(coroutine):
            callbacks = self.error_callbacks if error else self.callbacks

            callbacks.append(coroutine)

            def get_priority(callback):
                if hasattr(callback, "priority") and \
                        callback.priority is not None:
                    return -callback.priority

                return -priority

            callbacks.sort(key=get_priority)

            return coroutine

        for callback in callbacks:
            _register(callback)

        return _register

    def register_startup(self, *callbacks):
        """
        Register callbacks for startup of engine.

        :param callbacks: callbacks for registration
        :rtype: decorator for registration
        """

        def _register_startup(coroutine):
            self.startup_callbacks.append(coroutine)
            return coroutine

        for callback in callbacks:
            _register_startup(callback)

        return _register_startup

    def register_dispose(self, *callbacks):
        """
        Register callbacks for disposing resourses before shutting down
        engine.

        :param callbacks: callbacks for registration
        :rtype: decorator for registration
        """

        def _register_dispose(coroutine):
            self.dispose_callbacks.append(coroutine)
            return coroutine

        for callback in callbacks:
            _register_dispose(callback)

        return _register_dispose

    async def process(self, update, env):
        """
        Process passed update with passed :class:`.Environment`

        :param update: update to process
        :param env: :class:`.Environment` to process with
        """
        try:
            for callback in self.callbacks:
                if await callback(update, env) == "DONE":
                    break

        except Exception as e:  # pylint: disable=W0703
            logger.exception(
                "\"%s::%s\" on update %s from %s",
                sys.exc_info()[0].__name__, e, update, env.manager_type
            )

            env.exception = e

            if not self.error_callbacks:
                return await env.reply(
                    "Произошла ошибка! Приносим свои извинения."
                )

            for callback in self.error_callbacks:
                if await callback(update, env) == "DONE":
                    break

    async def startup(self, kutana):
        """Call initialization callbacks."""

        for callback in self.startup_callbacks:
            await callback(kutana, self.registered_plugins)

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        for callback in self.dispose_callbacks:
            await callback()
