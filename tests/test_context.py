import asyncio
import pytest
from asynctest import MagicMock, CoroutineMock
from kutana import Context


def test_reply_non_str():
    ctx = Context(backend=MagicMock(perform_send=CoroutineMock()))
    ctx.default_target_id = 1
    asyncio.get_event_loop().run_until_complete(ctx.reply(123))
    ctx.backend.perform_send.assert_called_with(1, '123', (), {})


def test_context():
    called = []

    class Backend:
        async def perform_send(self, target_id, message, attachments, kwargs):
            called.append(("ps", message))

        async def perform_api_call(self, method, kwargs):
            called.append(("pac", method, kwargs))

    ctx = Context(backend=Backend())
    ctx.default_target_id = 1

    asyncio.get_event_loop().run_until_complete(ctx.reply("hey1"))
    asyncio.get_event_loop().run_until_complete(ctx.send_message(1, "hey2"))
    asyncio.get_event_loop().run_until_complete(ctx.request("a", v="hey3"))

    assert called == [
        ("ps", "hey1"),
        ("ps", "hey2"),
        ("pac", "a", {"v": "hey3"}),
    ]

    called.clear()

    message = "a" * 4096 + "b" * 4096 + "c" * 4096

    asyncio.get_event_loop().run_until_complete(ctx.reply(message))

    assert called == [
        ("ps", message[:4096]),
        ("ps", message[4096: 4096 * 2]),
        ("ps", message[4096 * 2:]),
    ]


def test_lont_message_for_kwargs():
    ctx = Context(backend=CoroutineMock(perform_send=CoroutineMock()))
    ctx.default_target_id = 1

    asyncio.get_event_loop().run_until_complete(ctx.reply("a" * (4096 * 2 - 1)))

    ctx.backend.perform_send.assert_any_await(1, "a" * 4096, (), {})
    ctx.backend.perform_send.assert_any_await(1, "a" * 4095, (), {})


def test_dynamic_attributes():
    ctx = Context()

    ctx.var1 = "val1"
    ctx.var2 = "val2"

    assert ctx.var1 == "val1"
    assert ctx.var2 == "val2"
    assert ctx.get("var3") is None
    assert ctx.get("var3", "default_value_1") == "default_value_1"


def test_set_state():
    storage = {}

    class Storage:
        @staticmethod
        async def save(k, v):
            storage[k] = v

        @staticmethod
        async def load(k, d):
            return storage.get(k, d)

    class App:
        storage = Storage

    ctx = Context(app=App)

    # Happy path
    ctx.group_uid = "*gr"
    ctx.group_state_key = "_sg:*gr"
    ctx.user_uid = "*us"
    ctx.user_state_key = "_su:*us"

    async def test():
        await ctx.set_state(user_state="new_us_state")
        await ctx.set_state(group_state="new_gr_state")

    asyncio.get_event_loop().run_until_complete(test())

    assert storage[ctx.group_state_key] == "new_gr_state"
    assert storage[ctx.user_state_key] == "new_us_state"

    # Wrong update state 1
    ctx.group_uid = ""
    ctx.group_state_key = ""

    async def test():
        with pytest.raises(ValueError):
            await ctx.set_state(group_state="new_new_gr_state")

    asyncio.get_event_loop().run_until_complete(test())

    # Wrong update state 2
    ctx.user_uid = ""
    ctx.user_state_key = ""

    async def test():
        with pytest.raises(ValueError):
            await ctx.set_state(user_state="new_new_us_state")

    asyncio.get_event_loop().run_until_complete(test())

    assert storage["_sg:*gr"] == "new_gr_state"
    assert storage["_su:*us"] == "new_us_state"


def test_set_state_non_string():
    storage = {}

    class Storage:
        @staticmethod
        async def save(k, v):
            storage[k] = v

        @staticmethod
        async def load(k, d):
            return storage.get(k, d)

    class App:
        storage = Storage

    ctx = Context(app=App)

    async def test():
        with pytest.raises(ValueError):
            await ctx.set_state(0, None)

        with pytest.raises(ValueError):
            await ctx.set_state(None, 0)

        with pytest.raises(ValueError):
            await ctx.set_state(0, 0)

    asyncio.get_event_loop().run_until_complete(test())


def test_replace_method():
    calls = []

    async def replacement(self, message, attachments=(), **kwargs):
        calls.append((message, attachments, kwargs))

    ctx = Context()
    ctx.replace_method("reply", replacement)
    asyncio.get_event_loop().run_until_complete(ctx.reply("hey"))

    assert calls == [("hey", (), {})]

    with pytest.raises(ValueError):
        ctx.replace_method("a" * 64, lambda: 0)
