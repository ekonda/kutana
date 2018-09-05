from kutana.tools.structures import objdict
import shlex
import re


class Plugin():
    """Class for craeting extensions for kutana engine."""

    def __init__(self, **kwargs):
        self._callbacks = []
        self._callbacks_raw = []
        self._callbacks_dispose = []
        self._callback_startup = None

        self.order = 50

        for k, v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def done_if_none(value):
        """Return "DONE" if value is None. Otherwise return value."""

        if value is None:
            return "DONE"

        return value

    async def proc_update(self, update, eenv):
        """Method for processing updates."""

        if eenv.ctrl_type == "kutana":
            if update["update_type"] == "startup":
                if self._callback_startup:
                    await self._callback_startup(update["kutana"], update)

            return

        env = objdict(eenv=eenv, **eenv)

        if eenv.get("_cached_message"):
            message = eenv["_cached_message"]

        else:
            message = await eenv.convert_to_message(update, eenv)

            eenv["_cached_message"] = message

        if message is None:
            if not self._callbacks_raw:
                return

            arguments = {
                "env": env,
                "update": update
            }

            callbacks = self._callbacks_raw

        else:
            arguments = {
                "env": env,
                "message": message,
                "attachments": message.attachments
            }

            callbacks = self._callbacks

        for callback in callbacks:
            comm = await callback(**arguments)

            if comm == "DONE":
                return "DONE"

    async def dispose(self):
        """Free resources and prepare for shutdown."""

        for callback in self._callbacks_dispose:
            await callback()

    def add_callbacks(self, *callbacks):
        """Add callbacks for processing updates."""

        for callback in callbacks:
            self._callbacks.append(callback)

    def on_dispose(self):
        """Returns decorator for adding callbacks which is triggered when
        everything is going to shutdown.
        """

        def decorator(coro):
            self._callbacks_dispose.append(coro)

            return coro

        return decorator

    def on_startup(self):
        """Returns decorator for adding callbacks which is triggered
        at the startup of kutana. Decorated coroutine receives kutana
        object and some information in update.
        """

        def decorator(coro):
            self._callback_startup = coro

            return coro

        return decorator

    def on_raw(self):
        """Returns decorator for adding callbacks which is triggered
        every time when update can't be turned into `Message` or
        `Attachment` object. Arguments `env` and raw `update`
        is passed to callback.
        """

        def decorator(coro):
            self._callbacks_raw.append(coro)

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
                    comm = self.done_if_none(await coro(*args, **kwargs))

                    if comm == "DONE":
                        return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_has_text(self, *texts):
        """Returns decorator for adding callbacks which is triggered
        when the message contains any of the specified texts.

        Fills env for callback with:

        - "found_text" - text found in message.
        """

        def decorator(coro):
            check_texts = tuple(text.strip().lower() for text in texts) or ("",)

            async def wrapper(*args, **kwargs):
                check_text = kwargs["message"].text.strip().lower()

                for text in check_texts:
                    if text not in check_text:
                        continue

                    kwargs["env"]["found_text"] = text

                    comm = self.done_if_none(await coro(*args, **kwargs))

                    if comm == "DONE":
                        return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_startswith_text(self, *texts):
        """Returns decorator for adding callbacks which is triggered
        when the message starts with any of the specified texts.

        Fills env for callback with:

        - "body" - text without prefix.
        - "args" - text without prefix splitted in bash-like style.
        - "prefix" - prefix.
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
                kwargs["env"]["args"] = shlex.split(kwargs["env"]["body"])
                kwargs["env"]["prefix"] = kwargs["message"].text[:len(search_result)].strip()

                comm = self.done_if_none(await coro(*args, **kwargs))

                if comm == "DONE":
                    return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator

    def on_regexp_text(self, regexp, flags=0):
        """Returns decorator for adding callbacks which is triggered
        when the message matches the specified regular expression.

        Fills env for callback with:

        - "match" - match.
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

                comm = self.done_if_none(await coro(*args, **kwargs))

                if comm == "DONE":
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

                comm = self.done_if_none(await coro(*args, **kwargs))

                if comm == "DONE":
                    return "DONE"

            self.add_callbacks(wrapper)

            return wrapper

        return decorator
