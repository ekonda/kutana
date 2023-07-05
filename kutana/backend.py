class Backend:
    def get_identity(self):
        raise NotImplementedError

    async def on_start(self, app):
        pass

    async def on_shutdown(self, app):
        pass

    async def setup_context(self, context):
        pass

    async def acquire_updates(self, queue):
        raise NotImplementedError

    async def send_message(self, recipient_id, text=None, attachments=None, **kwargs):
        raise NotImplementedError

    async def request(self, method, kwargs):
        raise NotImplementedError
