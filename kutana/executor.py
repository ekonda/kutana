from kutana.logger import logger
import sys


class Executor:
    """Class performing update processing."""

    def __init__(self):
        self.callbacks = []
        self.error_callbacks = []

        self.registered_plugins = []

    def register_plugins(self, *plugins):
        """Register callbacks from plugins."""

        for plugin in plugins:
            if hasattr(plugin, "_prepare_callbacks"):
                self.register(*plugin._prepare_callbacks())

            if hasattr(plugin, "_prepare_callbacks_error"):  # pragma: no cover
                self.register(*plugin._prepare_callbacks_error(), error=True)

            self.registered_plugins.append(plugin)

    def register(self, *callbacks, priority=400, error=False):
        """Register callbacks."""

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

    async def __call__(self, update, eenv):
        """Process update from controller."""

        try:
            for cb in self.callbacks:
                comm = await cb(update, eenv)

                if comm == "DONE":
                    break

        except Exception as e:
            logger.exception(
                "\"{}::{}\" on update {} from {}".format(
                    sys.exc_info()[0].__name__, e, update, eenv.ctrl_type
                )
            )

            eenv["exception"] = e

            if not self.error_callbacks:
                if "reply" in eenv:
                    return await eenv.reply("Произошла ошибка! Приносим свои извинения.")

            for cb in self.error_callbacks:
                comm = await cb(update, eenv)

                if comm == "DONE":
                    break

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        for callback_owner in self.registered_plugins:
            if hasattr(callback_owner, "dispose"):
                await callback_owner.dispose()
