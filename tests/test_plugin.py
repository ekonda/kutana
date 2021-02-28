from unittest.mock import call
import pytest
from kutana import (
    Plugin, Message, Update, UpdateType, Attachment, HandlerResponse as hr,
)
from testing_tools import sync, make_kutana_no_run


def test_get_set():
    pl = Plugin("", attr1='value')
    pl.attr2 = lambda: "hey"
    assert pl.attr1 == "value"
    assert pl.attr2() == "hey"


def test_failed_get():
    pl = Plugin("")

    with pytest.raises(AttributeError):
        pl.bruh


def test_clever_on_commands():
    pl = Plugin("")
    pl.on_commands("bruh")


def test_matches():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_match(r"\d.\d")
    async def __(msg, ctx):
        await ctx.reply(ctx.match.group(0))

    @pl.on_match(r"(a|b|c).[a-z]")
    async def __(msg, ctx):
        await ctx.reply(ctx.match.group(0))
        await ctx.reply(ctx.match.group(1))

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, "123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "abc", (), 1, 0, 0, 0))
    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert debug.answers[1][0] == ("123", (), {})
    assert debug.answers[1][1] == ("abc", (), {})
    assert debug.answers[1][2] == ("a", (), {})


def test_any_message():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_messages()
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, "123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "abc", (), 1, 0, 0, 0))
    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert debug.answers[1][0] == ("123", (), {})
    assert debug.answers[1][1] == ("abc", (), {})


def test_any_unprocessed_message():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_commands(["abc"])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    @pl.on_unprocessed_messages()
    async def __(msg, ctx):
        await ctx.reply(msg.text * 2)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".abc", (), 1, 0, 0, 0))
    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert debug.answers[1][0] == (".123" * 2, (), {})
    assert debug.answers[1][1] == (".abc", (), {})


def test_any_update():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    received = []

    @pl.on_updates()
    async def __(upd, ctx):
        received.append(upd.raw)

    app.add_plugin(pl)

    hu(Update('a', UpdateType.UPD))
    hu(Update('b', UpdateType.UPD))
    assert hu(Message(None, UpdateType.MSG, ".123", (), 1, 0, 0, 0)) == hr.SKIPPED

    assert received[0] == 'a'
    assert received[1] == 'b'


def test_any_unprocessed_update():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    received = []

    @pl.on_updates()
    async def __(upd, ctx):
        if upd.raw == 'a':
            return hr.SKIPPED
        received.append(upd.raw)

    @pl.on_unprocessed_updates()
    async def __(upd, ctx):
        received.append(upd.raw * 2)

    app.add_plugin(pl)

    hu(Update('a', UpdateType.UPD))
    hu(Update('b', UpdateType.UPD))
    assert hu(Message(None, UpdateType.MSG, ".123", (), 1, 0, 0, 0)) == hr.SKIPPED

    assert received[0] == 'aa'
    assert received[1] == 'b'


def test_router_priority():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    received = []

    @pl.on_updates(router_priority=10)
    async def __(upd, ctx):
        received.append(upd.raw * 2)

    @pl.on_unprocessed_updates(priority=1, router_priority=10)
    async def __(upd, ctx):
        received.append(upd.raw * 3)

    @pl.on_updates(router_priority=20)
    async def __(upd, ctx):
        if upd.raw == 'a':
            return hr.SKIPPED
        received.append(upd.raw)

    app.add_plugin(pl)

    hu(Update('a', UpdateType.UPD))
    hu(Update('b', UpdateType.UPD))
    assert hu(Message(None, UpdateType.MSG, ".123", (), 1, 0, 0, 0)) == hr.SKIPPED

    assert received[0] == 'aaa'
    assert received[1] == 'b'


def test_commands():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_commands(["echo", "ec"])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".echo 123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".ec abc", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".echo", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".ec\n123", (), 1, 0, 0, 0))

    hu(Message(None, UpdateType.MSG, ".ecabc", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".e cabc", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "abc", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "echo abc", (), 1, 0, 0, 0))

    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert len(debug.answers[1]) == 4
    assert debug.answers[1][0] == (".echo 123", (), {})
    assert debug.answers[1][1] == (".ec abc", (), {})
    assert debug.answers[1][2] == (".echo", (), {})
    assert debug.answers[1][3] == (".ec\n123", (), {})

def test_commands_with_spaces():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_commands(["echo", "ec"])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, " . echo 123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ". echo 123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".\nec abc", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 3
    assert debug.answers[1][0] == (" . echo 123", (), {})
    assert debug.answers[1][1] == (". echo 123", (), {})
    assert debug.answers[1][2] == (".\nec abc", (), {})

def test_command_full_body():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_commands(["echo"])
    async def __(msg, ctx):
        await ctx.reply(ctx.body)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".echo abc\nabc\nabc", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 1
    assert debug.answers[1][0] == ("abc\nabc\nabc", (), {})


def test_attachments():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_attachments(["image", "voice"])
    async def __(msg, ctx):
        await ctx.reply(msg.text)

    app.add_plugin(pl)

    image = Attachment("", "image", "", None, "", None, "present")
    voice = Attachment("", "voice", "", None, "", None, "present")
    sticker = Attachment("", "sticker", "", None, "", None, "present")

    hu(Message(None, UpdateType.MSG, "i", (image,), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "v", (voice,), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "vi", (voice, image), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "si", (sticker, image,), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, "s", (sticker,), 1, 0, 0, 0))

    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert len(debug.answers[1]) == 4
    assert debug.answers[1][0] == ("i", (), {})
    assert debug.answers[1][1] == ("v", (), {})
    assert debug.answers[1][2] == ("vi", (), {})
    assert debug.answers[1][3] == ("si", (), {})


def test_on_start():
    pl = Plugin("API")
    pl.app = 2

    @pl.on_start()
    async def __():
        return 1

    # Deprecated version
    @pl.on_start()
    async def __(app):
        return app

    assert sync(pl._handlers['start'][0].handle()) == 1
    assert sync(pl._handlers['start'][1].handle()) == 2


def test_event_handlers_order():
    app, __, __ = make_kutana_no_run()

    pl = Plugin("", called=[])

    @pl.on_before(priority=5)
    async def __(upd, ctx):
        pl.called.append(2)

    @pl.on_before(priority=0)
    async def __(upd, ctx):
        pl.called.append(3)

    @pl.on_before(priority=10)
    async def __(upd, ctx):
        pl.called.append(1)

    @pl.on_before(priority=-10)
    async def __(upd, ctx):
        pl.called.append(4)

    app.add_plugin(pl)

    sync(app._handle_event("before", None, None))

    assert pl.called == [1, 2, 3, 4]


def test_storage():
    app, __, __ = make_kutana_no_run()

    pl = Plugin("", storage={})
    pl.app = app
    assert pl.storage == {}

    pl = Plugin("", storage='default')
    pl.app = app
    assert pl.storage == app._storages['default']

    pl = Plugin("", storage='unknown')
    pl.app = app
    assert pl.storage is None


def test_sender_states():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")
    pl.app = app

    @pl.on_commands(["a"])
    @pl.expect_sender(state="")
    async def __(msg, ctx):
        await ctx.sender.update({"state": "state"})
        await ctx.reply("ok:a")

    @pl.on_commands(["b"])
    @pl.expect_sender(state="state")
    async def __(msg, ctx):
        await ctx.sender.update({"state": ""})
        await ctx.reply("ok:b")

    @pl.on_commands(["a"])
    @pl.expect_sender(state="other_state")
    async def __(msg, ctx):
        await ctx.sender.update({"state": ""})
        await ctx.reply("ok:b")

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".a", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".b", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".b", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".a", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 3
    assert debug.answers[1].count(("ok:a", (), {})) == 2
    assert debug.answers[1].count(("ok:b", (), {})) == 1
    assert debug.answers[1][-1] == ("ok:a", (), {})


def test_receiver_states():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")
    pl.app = app

    @pl.on_commands(["a"])
    @pl.expect_receiver(state="")
    async def __(msg, ctx):
        await ctx.receiver.update({"state": "state"})
        await ctx.reply("ok:a")

    @pl.on_commands(["b"])
    @pl.expect_receiver(state="state")
    async def __(msg, ctx):
        await ctx.receiver.update({"state": ""})
        await ctx.reply("ok:b")

    @pl.on_commands(["a"])
    @pl.expect_receiver(state="other_state")
    async def __(msg, ctx):
        await ctx.receiver.update({"state": ""})
        await ctx.reply("ok:b")

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".a", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".b", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".b", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".a", (), 1, 0, 0, 0))

    assert len(debug.answers[1]) == 3
    assert debug.answers[1].count(("ok:a", (), {})) == 2
    assert debug.answers[1].count(("ok:b", (), {})) == 1
    assert debug.answers[1][-1] == ("ok:a", (), {})
