import pytest
from kutana import (
    Plugin, Message, Update, UpdateType, Attachment, HandlerResponse as hr,
)
from testing_tools import make_kutana_no_run


def make_message_update(payload):
    return {
        "object": {
            "message": {
                "payload": payload,
            },
        },
    }


def make_message_action(action_type, member_id, text, email, photo):
    obj = {
        "object": {
            "message": {
                "action": {
                    "type": action_type,
                }
            },
        },
    }
    if action_type in ("chat_photo_update", "chat_photo_remove", "chat_create"):
        obj["object"]["message"]["action"]["photo"] = photo

    if action_type in ("chat_title_update", "chat_create"):
        obj["object"]["message"]["action"]["text"] = text

    if action_type in ("chat_invite_user", "chat_kick_user",
                       "chat_unpin_message", "chat_pin_message", "chat_invite_user_by_link"):
        obj["object"]["message"]["action"]["member_id"] = member_id

    if action_type in ("chat_invite_user", "chat_kick_user") and isinstance(member_id, int) and member_id < 0:
        obj["object"]["message"]["action"]["email"] = email

    return obj


def test_on_payloads():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_payloads([{"command": "test"}])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    raw1 = make_message_update('{"command": "test"}')
    raw2 = make_message_update('{"command": "error"}')

    hu(Message(raw1, UpdateType.MSG, "hey1", (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, "hey2", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 1
    assert debug.answers[1][0] == ("hey1", (), {})


def test_on_payloads_types():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_payloads([{"command": {"why": "test"}}, "txt"])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    raw1 = make_message_update('{"command": {"why": "test"}}')
    raw2 = make_message_update('{"command": []}')
    raw3 = make_message_update('{"command": [{"a": 1}]}')
    raw4 = make_message_update('"txt"')
    raw5 = make_message_update("error")

    hu(Message(raw1, UpdateType.MSG, "hey1", (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, "hey2", (), 1, 0, 0, 0))
    hu(Message(raw3, UpdateType.MSG, "hey3", (), 1, 0, 0, 0))
    hu(Message(raw4, UpdateType.MSG, "hey4", (), 1, 0, 0, 0))
    hu(Message(raw5, UpdateType.MSG, "hey5", (), 1, 0, 0, 0))

    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert len(debug.answers[1]) == 2
    assert debug.answers[1][0] == ("hey1", (), {})
    assert debug.answers[1][1] == ("hey4", (), {})


def test_on_message_actions():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_message_actions(['chat_title_update', 'chat_create'])
    async def __(msg, ctx):
        await ctx.reply(msg.raw["object"]["message"]["action"]["text"])

    app.add_plugin(pl)

    raw1 = make_message_action('chat_invite_user_by_link', 1, None, None, None)
    raw2 = make_message_action('chat_title_update', 1, 'they1', None, None)

    hu(Message(raw1, UpdateType.MSG, 'hey1', (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, 'hey2', (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 1
    assert debug.answers[1][0] == ("they1", (), {})


def test_on_message_actions_types():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_message_actions(["chat_photo_remove"])
    async def __(msg, ctx):
        await ctx.reply(msg.raw['object']['message']["action"]["photo"]["photo_50"])

    @pl.vk.on_message_actions(['chat_invite_user'])
    async def __(msg, ctx):
        if msg.raw['object']['message']['action']['member_id'] < 0:
            await ctx.reply(msg.raw['object']['message']['action']['email'])

    app.add_plugin(pl)

    raw1 = make_message_action('chat_photo_update', 1, None, None, {
        "photo_50": "http://example.com/50",
        "photo_100": "http://example.com/100",
        "photo_200": "http://example.com/200",
    })
    raw2 = make_message_action('chat_photo_remove', 1, None, None, {
        "photo_50": "http://example.com/50",
        "photo_100": "http://example.com/100",
        "photo_200": "http://example.com/200",
    })
    raw3 = make_message_action('chat_title_update', 1, 'title1', None, None)
    raw4 = make_message_action('chat_invite_user', -1, None, "example1@mail.com", None)
    raw5 = make_message_action('chat_kick_user', -1, None, "example2@mail.com", None)
    raw6 = make_message_update("error")

    hu(Message(raw1, UpdateType.MSG, "hey1", (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, "hey2", (), 1, 0, 0, 0))
    hu(Message(raw3, UpdateType.MSG, "hey3", (), 1, 0, 0, 0))
    hu(Message(raw4, UpdateType.MSG, "hey4", (), 1, 0, 0, 0))
    hu(Message(raw5, UpdateType.MSG, "hey5", (), 1, 0, 0, 0))
    hu(Message(raw6, UpdateType.MSG, "hey6", (), 1, 0, 0, 0))

    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert len(debug.answers[1]) == 2
    assert debug.answers[1][0] == ("http://example.com/50", (), {})
    assert debug.answers[1][1] == ("example1@mail.com", (), {})


def test_on_payloads_exact():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_payloads([{"command": "echo"}])
    async def __(msg, ctx):
        await ctx.reply(ctx.payload["text"])

    app.add_plugin(pl)

    raw1 = make_message_update('{"command": "echo", "text": "hello"}')
    raw2 = make_message_update('{"command": "echo", "text": "sup"}')

    hu(Message(raw1, UpdateType.MSG, "hey1", (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, "hey2", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 2
    assert debug.answers[1][0] == ("hello", (), {})
    assert debug.answers[1][1] == ("sup", (), {})
