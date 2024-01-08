import json

from ...helpers import pick, uniq_by
from ...router import MapRouter
from ...update import Message


class VkontakteChatActionRouter(MapRouter):
    def extract_keys(self, context):
        if not isinstance(context.update, Message):
            return ()

        if context.backend.get_identity() != "vk":
            return ()

        chat_action = context.update.raw["object"]["message"].get("action")
        if not chat_action:
            return ()

        context.chat_action = chat_action

        return (chat_action["type"],)


class VkontaktePayloadRouter(MapRouter):
    def __init__(self, priority=0):
        super().__init__(priority)
        self._possible_key_shapes = set()

    def _update_possible_key_shapes(self, key):
        if not isinstance(key, dict):
            return

        self._possible_key_shapes = uniq_by(
            [
                *self._possible_key_shapes,
                tuple(sorted(key.keys())),
            ]
        )

    def add_handler(self, key, handler):
        self._update_possible_key_shapes(key)
        return super().add_handler(self._to_hashable(key), handler)

    @staticmethod
    def _merge_routers(target, source):
        super()._merge_routers(target, source)
        target._possible_key_shapes.update(source._possible_key_shapes)

    def _to_hashable(self, value):
        if isinstance(value, dict):
            return tuple((k, self._to_hashable(v)) for k, v in sorted(value.items()))

        if isinstance(value, list):
            return tuple(self._to_hashable(item) for item in value)

        return value

    def extract_keys(self, context):
        if not isinstance(context.update, Message):
            return ()

        if context.backend.get_identity() != "vk":
            return ()

        raw_payload = context.update.raw["object"]["message"].get("payload")
        if not raw_payload:
            return ()

        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return ()

        context.payload = payload

        if isinstance(payload, dict):
            return (
                self._to_hashable(pick(payload, possible_key_shape))
                for possible_key_shape in self._possible_key_shapes
            )
        else:
            return (self._to_hashable(payload),)


class VkontakteCallbackRouter(VkontaktePayloadRouter):
    def extract_keys(self, context):
        if isinstance(context.update, Message):
            return ()

        if context.backend.get_identity() != "vk":
            return ()

        if context.update["type"] != "message_event":
            return ()

        payload = context.update["object"]["payload"]

        context.payload = payload

        async def _send_message_event_answer(event_data, **kwargs):
            return await context.request(
                "messages.sendMessageEventAnswer",
                {
                    "event_id": context.update["object"]["event_id"],
                    "user_id": context.update["object"]["user_id"],
                    "peer_id": context.update["object"]["peer_id"],
                    "event_data": json.dumps(event_data),
                    **kwargs,
                },
            )

        context.send_message_event_answer = _send_message_event_answer

        if isinstance(payload, dict):
            return (
                self._to_hashable(pick(payload, possible_key_shape))
                for possible_key_shape in self._possible_key_shapes
            )
        else:
            return (self._to_hashable(payload),)


class VkontaktePluginExtension:
    def __init__(self, plugin):
        self._plugin = plugin

    def on_chat_actions(
        self,
        kinds,
        priority=0,
    ):
        """
        Return decorator for registering handler that will be called if
        incoming update is a message with action (only for chats).

        Context is automatically populated with following values:

        - "action" - chat action object.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro):
            chat_action_router = VkontakteChatActionRouter(priority=priority)
            for kind in kinds:
                chat_action_router.add_handler(kind, coro)

            self._plugin._routers.append(chat_action_router)

            return coro

        return decorator

    def on_payloads(
        self,
        payloads,
        priority=0,
    ):
        """
        Return decorator for registering handler that will be called if
        incoming update is a message with specified value in payload.
        Payload is treated as JSON-encoded value. Excessive fields in
        payload are ignored. Use strings or lists for exact matching.

        Context is automatically populated with following values:

        - "payload" - chat action object.

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro):
            payload_router = VkontaktePayloadRouter(priority=priority)
            for payload in payloads:
                payload_router.add_handler(payload, coro)

            self._plugin._routers.append(payload_router)

            return coro

        return decorator

    def on_callbacks(
        self,
        payloads,
        priority=0,
    ):
        """
        Return decorator for registering handler that will be called if
        incoming update is a message_event with specified value in payload.
        Excessive fields in payload are ignored. Use strings or lists for
        exact matching.

        Context is automatically populated with following values:

        - "payload" - callback payload value.
        - "send_message_event_answer" - helper method for "messages.sendMessageEventAnswer".

        See :class:`kutana.plugin.Plugin.on_commands` for details
        about 'priority' and return values.
        """

        def decorator(coro):
            callback_router = VkontakteCallbackRouter(priority=priority)
            for payload in payloads:
                callback_router.add_handler(payload, coro)

            self._plugin._routers.append(callback_router)

            return coro

        return decorator
