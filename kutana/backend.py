class Backend:
    async def on_start(self, app):
        pass

    async def on_shutdown(self, app):
        pass

    def prepare_context(self, ctx):
        pass

    async def perform_updates_request(self, submit_update):
        # TODO: Rename to "acquire_updates"
        raise NotImplementedError

    async def perform_send(self, target_id, message, attachments, kwargs):
        # TODO: Rename to "send_message"
        raise NotImplementedError

    async def perform_api_call(self, method, kwargs):
        # TODO: Rename to "api_request"
        raise NotImplementedError

    @classmethod
    def get_identity(cls):
        return cls.__name__.lower()
