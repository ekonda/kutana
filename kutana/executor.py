"""Class performing callbacks management."""


from .logger import logger
from .utils import sort_callbacks


class Executor:

    """Class performing callbacks management."""

    def __init__(self):
        self.callbacks = []

        self.startup_callbacks = []
        self.dispose_callbacks = []

        self.registered_plugins = []

    def register_plugins(self, plugins):
        """
        Register plugins' callbacks in executor.

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

    def register(self, *callbacks, priority=400):
        """
        Register callbacks for processing updates or errors with specified
        priority.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        :param error: True if registration for processing errors
        """

        for callback in callbacks:
            self.callbacks.append((priority, callback))

        sort_callbacks(self.callbacks)

    def register_startup(self, *callbacks, priority=0):
        """
        Register callbacks for startup of engine.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        """

        for callback in callbacks:
            self.startup_callbacks.append((priority, callback))

        sort_callbacks(self.startup_callbacks)

    def register_dispose(self, *callbacks, priority=0):
        """
        Register callbacks for disposing resourses before shutting down
        engine.

        :param callbacks: callbacks for registration
        :param priority: priority of callbacks
        """

        for callback in callbacks:
            self.dispose_callbacks.append((priority, callback))

        sort_callbacks(self.dispose_callbacks)

    async def process(self, update, env):
        """
        Process passed update with callbakcs inside of passed
        :class:`.Environment`.

        :param update: update to process
        :param env: :class:`.Environment` to process with
        """

        try:
            await env.process(update, self.callbacks)

        except Exception as e:  # pylint: disable=W0703
            await env.reply(
                "Произошла крайне критическая ошибка. Сообщите об этом "
                "администратору."
            )

            logger.exception(e)

    async def startup(self, kutana):
        """Call initialization callbacks."""

        for _, callback in self.startup_callbacks:
            await callback(kutana, self.registered_plugins)

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        for _, callback in self.dispose_callbacks:
            await callback()
