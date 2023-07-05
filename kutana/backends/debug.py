import asyncio

from ..backend import Backend
from ..kutana import Kutana
from ..plugin import Plugin
from ..update import Message, RecipientKind


class Debug(Backend):
    def __init__(self, updates, identity=None, **kwargs):
        super().__init__(**kwargs)

        self.updates = [self._make_update(*args) for args in updates]
        self._update_processed = 0

        self.messages = []
        self.requests = []

        self._identity = identity

    def get_identity(self):
        return self._identity

    @classmethod
    async def handle_updates(cls, plugins, updates, identity=None):
        # create backend
        backend = cls(updates, identity=identity)

        # create plugin that will stop applition when needed
        stopper_plugin = Plugin("_stopper")

        def _update_processed():
            backend._update_processed += 1
            if backend._update_processed >= len(backend.updates):
                future.cancel()

        @stopper_plugin.on_completion()
        async def _(context):
            _update_processed()

        @stopper_plugin.on_exception()
        async def _(context, exception):
            _update_processed()

        # create application, fill it with plugins and backends
        app = Kutana()

        app.add_backend(backend)

        app.add_plugin(stopper_plugin)

        for plugin in plugins:
            app.add_plugin(plugin)

        # run application (save to variable for stopper)
        future = asyncio.ensure_future(app._run())

        try:
            await future
        except asyncio.CancelledError:
            pass
        finally:
            await app._shutdown_wrapper()

        # return used application and backend
        return app, backend

    def _make_update(self, text, sender_id, recipient_id, attachments, raw=None):
        return Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            recipient_kind=RecipientKind.PRIVATE_CHAT,
            text=text,
            attachments=attachments,
            date=0,
            raw=raw,
        )

    async def acquire_updates(self, queue):
        while self.updates:
            await queue.put((self.updates.pop(0), self))

    async def send_message(self, target_id, message, attachments, **kwargs):
        self.messages.append((target_id, str(message), attachments, kwargs))

    async def request(self, method, kwargs):
        self.requests.append((method, kwargs))
