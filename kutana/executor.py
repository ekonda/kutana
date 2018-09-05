from kutana.logger import logger
import sys


class Executor:
    """Class performing update processing."""

    def __init__(self):
        self.callbacks = []
        self.error_callbacks = []

        self.callbacks_owners = []

    def add_callbacks_from(self, executor):
        """Updates with callbacks from other executor."""

        self.callbacks += executor.callbacks
        self.error_callbacks += executor.error_callbacks

        self.callbacks_owners += executor.callbacks_owners

    def register_plugins(self, *plugins):
        """Register callbacks from plugins."""

        for plugin in plugins:
            if hasattr(plugin, "proc_update"):
                self.register(plugin.proc_update)

            if hasattr(plugin, "proc_error"):  # pragma: no cover
                self.register(plugin.proc_error, error=True)

    def register(self, *callbacks, error=False):
        """Register callbacks."""

        def _register(coroutine):
            if error:
                self.error_callbacks.append(coroutine)

            else:
                self.callbacks.append(coroutine)

            return coroutine

        for callback in callbacks:
            if hasattr(callback, "__self__"):
                self.callbacks_owners.append(callback.__self__)

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
                "\"{}::{}\"on update {} from {}".format(
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

        for callback_owner in self.callbacks_owners:
            if hasattr(callback_owner, "dispose"):
                await callback_owner.dispose()
