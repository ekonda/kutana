class Backend:
    def __init__(self, name=None, active=True):
        self.name = name
        self._active = active

    @property
    def active(self):
        return self._active

    async def on_start(self, app):
        pass

    async def on_shutdown(self, app):
        pass

    def prepare_context(self, ctx):
        pass

    async def acquire_updates(self, submit_update):
        raise NotImplementedError

    async def execute_send(self, target_id, message, attachments, kwargs):
        raise NotImplementedError

    async def execute_request(self, method, kwargs):
        raise NotImplementedError

    @classmethod
    def get_identity(cls):
        return cls.__name__.lower()
