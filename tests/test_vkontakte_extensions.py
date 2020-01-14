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


def test_on_payload():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_payload([{"command": "test"}])
    async def _(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    raw1 = make_message_update('{"command": "test"}')
    raw2 = make_message_update('{"command": "error"}')

    hu(Message(raw1, UpdateType.MSG, "hey1", (), 1, 0, 0, 0))
    hu(Message(raw2, UpdateType.MSG, "hey2", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 1
    assert debug.answers[1][0] == ("hey1", (), {})


def test_on_payload_types():
    app, debug, hu = make_kutana_no_run(backend_source="vkontakte")

    pl = Plugin("")

    @pl.vk.on_payload([{"command": {"why": "test"}}, "txt"])
    async def _(msg, ctx):
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
