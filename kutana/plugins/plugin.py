from kutana.plugins.converters import get_convert_to_message
from kutana.tools.structures import objdict
import re


class Plugin():
    """Class for craeting extensions for kutana engine."""

    def __init__(self):
        self.callbacks = []
        self.callbacks_raw = []
        self.callbacks_dispose = []
        self.callback_startup = None

        self.order = 50

        self.executor = None

    async def on_message(self, controller_type, update, extenv):
        """Method for processing updates."""

        if controller_type == "kutana":
            if update["update_type"] == "startup":
                if self.callback_startup:
                    await self.callback_startup(update["kutana"], update)

            return

        env = objdict()
        extenv.controller_type = controller_type

        arguments = {
            "message": "",
            "attachments": [],
            "env": env,
            "extenv": extenv
        }

        convert_to_message = get_convert_to_message(controller_type)

        isNotMessageOrAttachment = await convert_to_message(
                arguments,
                update,
                env,
                extenv
        )

        if isNotMessageOrAttachment:
            del arguments["message"]
            del arguments["attachments"]

            arguments["update"] = update

            callbacks = self.callbacks_raw

        else:
            callbacks = self.callbacks

        for callback in callbacks:
            comm = await callback(**arguments)

            if comm == "DONE":
                return "DONE"

    async def dispose(self):
        """Free resourses and prepare for shutdown."""

        for callback in self.callbacks_dispose:
            await callback()

    def add_callbacks(self, *callbacks):
        """Add callbacks for processing updates."""

        for callback in callbacks:
            self.callbacks.append(callback)

    def on_dispose(self):
        """Returns decorator for adding callbacks which is triggered when
        everything is going to shutdown.
        """

        def decorator(coro):
            self.callbacks_dispose.append(coro)

            return coro

        return decorator

    def on_startup(self):
        """Returns decorator for adding callbacks which is triggered
        at the startup of kutana. Decorated coroutine receives kutana
        object and some information in update.
        """

        def decorator(coro):
            self.callback_startup = coro

            return coro

        return decorator

    def on_raw(self):
        """Returns decorator for adding callbacks which is triggered
        every time when update can't be turned into `Message` or
        `Attachment` object. Raw update is passed to callback.
        """

        def decorator(coro):
            self.callbacks_raw.append(coro)

            return coro

        return decorator

    def on_text(self, *texts):
        """Returns decorator for adding callbacks which is triggered
        when the message and any of the specified text are fully matched.
        """

        def decorator(coro):
            check_texts = list(text.strip().lower() for text in texts)

            async def wrapper(*args, **kwargs):
                if kwargs["message"].text.strip().lower() in check_texts:
                    await coro(*args, **kwargs)

                    return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_has_text(self, *texts):
        """Returns decorator for adding callbacks which is triggered
        when the message contains any of the specified texts.
        """

        def decorator(coro):
            check_texts = tuple(text.strip().lower() for text in texts) or ("",)

            async def wrapper(*args, **kwargs):
                check_text = kwargs["message"].text.strip().lower()

                if any(text in check_text for text in check_texts):
                    await coro(*args, **kwargs)

                    return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_startswith_text(self, *texts):
        """Returns decorator for adding callbacks which is triggered
        when the message starts with any of the specified texts.
        """

        def decorator(coro):
            check_texts = tuple(text.lstrip().lower() for text in texts)

            def search_prefix(message):
                for text in check_texts:
                    if message.startswith(text):
                        return text

                return None

            async def wrapper(*args, **kwargs):
                search_result = search_prefix(kwargs["message"].text.lower())

                if search_result is None:
                    return

                kwargs["env"]["body"] = kwargs["message"].text[len(search_result):].strip()
                kwargs["env"]["prefix"] = kwargs["message"].text[:len(search_result)].strip()

                await coro(*args, **kwargs)

                return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_regexp_text(self, regexp, flags=0):
        """Returns decorator for adding callbacks which is triggered
        when the message matches the specified regular expression.
        """

        if isinstance(regexp, str):
            compiled = re.compile(regexp, flags=flags)

        else:
            compiled = regexp

        def decorator(coro):
            async def wrapper(*args, **kwargs):
                match = compiled.match(kwargs["message"].text)

                if not match:
                    return

                kwargs["env"]["match"] = match

                await coro(*args, **kwargs)

                return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_attachment(self, *types):
        """Returns decorator for adding callbacks which is triggered
        when the message has attachments of the specified type
        (if no types specified, then any attachments).
        """

        def decorator(coro):
            async def wrapper(*args, **kwargs):
                if not kwargs["attachments"]:
                    return

                if types:
                    for a in kwargs["attachments"]:
                        if a.type in types:
                            break
                    else:
                        return

                await coro(*args, **kwargs)

                return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator
