import asyncio
import pytest
from asynctest import MagicMock, CoroutineMock
from kutana import Context


def test_reply_non_str():
    ctx = Context(backend=MagicMock(execute_send=CoroutineMock()))
    ctx.default_target_id = 1
    asyncio.get_event_loop().run_until_complete(ctx.reply(123))
    ctx.backend.execute_send.assert_called_with(1, '123', (), {})


def test_context():
    called = []

    class Backend:
        async def execute_send(self, target_id, message, attachments, kwargs):
            called.append(("ps", message))

        async def execute_request(self, method, kwargs):
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
    ctx = Context(backend=CoroutineMock(execute_send=CoroutineMock()))
    ctx.default_target_id = 1

    asyncio.get_event_loop().run_until_complete(ctx.reply("a" * (4096 * 2 - 1)))

    ctx.backend.execute_send.assert_any_await(1, "a" * 4096, (), {})
    ctx.backend.execute_send.assert_any_await(1, "a" * 4095, (), {})


def test_dynamic_attributes():
    ctx = Context()

    ctx.var1 = "val1"
    ctx.var2 = "val2"

    assert ctx.var1 == "val1"
    assert ctx.var2 == "val2"
    assert ctx.get("var3") is None
    assert ctx.get("var3", "default_value_1") == "default_value_1"


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
