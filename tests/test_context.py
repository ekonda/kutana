from unittest.mock import AsyncMock, Mock

from kutana import Context, Message, RecipientKind


async def test_reply_to_update():
    update = Message(
        "someone", "michaelkrukov", RecipientKind.PRIVATE_CHAT, "", [], 0, {}
    )
    context = Context(None, update, AsyncMock())

    await context.reply("Sup")
    context.backend.send_message.assert_awaited_with("michaelkrukov", "Sup", None)


async def test_reply_to_update_overwrite():
    context = Context(None, None, AsyncMock())
    context.recipient_id = "michaelkrukov"

    await context.reply("Sup")
    context.backend.send_message.assert_awaited_with("michaelkrukov", "Sup", None)


async def test_reply_with_large_text():
    context = Context(None, None, AsyncMock())
    context.recipient_id = "michaelkrukov"

    await context.reply("a" * 3 * 4096)
    context.backend.send_message.assert_awaited_with("michaelkrukov", "a" * 4096, None)


async def test_reply_with_kwargs():
    context = Context(None, None, AsyncMock())
    context.recipient_id = "michaelkrukov"

    await context.reply("Sup", mood="scared")
    context.backend.send_message.assert_awaited_with(
        "michaelkrukov", "Sup", None, mood="scared"
    )


async def test_unique_ids():
    update = Message(
        "someone", "michaelkrukov", RecipientKind.PRIVATE_CHAT, "", [], 0, {}
    )
    context = Context(None, update, AsyncMock(get_identity=Mock(return_value="b")))

    assert context.recipient_unique_id == "b:r:michaelkrukov"
    assert context.sender_unique_id == "b:s:someone"


async def test_unique_ids_overwrites():
    context = Context(None, None, AsyncMock(get_identity=Mock(return_value="b")))
    context.sender_id = "someone"
    context.recipient_id = "michaelkrukov"

    assert context.recipient_unique_id == "b:r:michaelkrukov"
    assert context.sender_unique_id == "b:s:someone"


def test_request():
    context = Context(None, None, Mock())
    assert context.request == context.backend.request


def test_custom_attributes():
    context = Context(None, None, None)
    context.attribute1 = "value1"
    context.attribute2 = "value2"
    assert context.attribute1 == "value1"
    assert context.attribute2 == "value2"
