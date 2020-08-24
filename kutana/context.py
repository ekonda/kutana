import types
from .update import UpdateType as ut, ReceiverType as rt


class Context:
    """
    Use Context.create for instantiation of Context object. This object
    can store ane attributes provided by routers or other plugins.

    :ivar ~.app: Context's kutana application.
    :ivar ~.update: Update currently being processed.
    :ivar ~.backend: Backend who created update.
    :ivar ~.config: Application's configuration
    :ivar ~.default_target_id: Default receiver of responses
    """

    def __init__(self, app=None, config=None, update=None, backend=None):
        self.app = app
        self.update = update
        self.backend = backend
        self.config = config

        self.default_target_id = None

    @staticmethod
    async def create(app=None, config=None, update=None, backend=None):
        """Create context with specified parameters."""

        ctx = Context(
            app=app,
            config=config,
            update=update,
            backend=backend,
        )

        if update.type == ut.MSG:
            if update.receiver_type == rt.MULTI:
                ctx.default_target_id = update.receiver_id
            else:
                ctx.default_target_id = update.sender_id

        return ctx

    def get(self, name, default=None):
        return getattr(self, name, default)

    def replace_method(self, method_name, method):
        """
        Replaces this instance's method with specified name with passed method.

        Example:

        .. code-block:: python

            async def replacement(self, message, attachments=(), **kwargs):
                print(message)
            ctx = Context()
            ctx.replace_method("reply", replacement)
            await ctx.reply("hey")  # will print "hey"

        .. note::

            Many methods are coroutine, so you should replace coroutines with
            coroutines and normal functions with functions.

        :param method_name: method's name to replace
        :param method: method to replace with
        """

        if not callable(getattr(self, method_name, None)):
            raise ValueError(f"No method with name '{method_name}'")

        setattr(self, method_name, types.MethodType(method, self))

    @staticmethod
    def split_large_text(text, length=4096):
        """
        Split text into chunks with specified length.

        :param text: text for splitting
        :param length: maximum size for one chunk
        :returns: tuple of chunks
        """

        text = str(text)

        yield text[0: length]

        for i in range(length, len(text), length):
            yield text[i: i + length]

    async def request(self, method, **kwargs):
        """Perform request to backend's API and return response."""

        return await self.backend.perform_api_call(
            method,
            kwargs,
        )

    async def reply(self, message, attachments=(), **kwargs):
        """
        Reply with specified message and attachments. Other kwargs are
        passed to the backend. Often as additional arguments to sending the
        message.

        If message is too long - it will be splitted.
        """

        return await self.send_message(
            self.default_target_id,
            message,
            attachments,
            **kwargs
        )

    async def send_message(self, target_id, message, attachments=(), **kwargs):
        """
        Send message to specified target_id with specifiend message and
        attachments. Other kwargs are passed to the backend. Often as
        additional arguments to sending the message.

        If message is too long - it will be splitted.
        """

        responses = []

        parts = tuple(self.split_large_text(message))

        for part in parts[:-1]:
            responses.append(await self.backend.perform_send(
                target_id,
                part,
                (),
                {},
            ))

        responses.append(await self.backend.perform_send(
            target_id,
            parts[-1],
            attachments,
            kwargs,
        ))

        return responses
