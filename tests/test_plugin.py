import pytest
from kutana import (
    Plugin, Message, Update, UpdateType, Attachment, HandlerResponse as hr,
)
from testing_tools import make_kutana_no_run


def test_get_set():
    pl = Plugin("")
    pl.attr = lambda: "hey"
    assert pl.attr() == "hey"


def test_failed_get():
    pl = Plugin("")

    with pytest.raises(AttributeError):
        pl.bruh


def test_failed_on_commands():
    pl = Plugin("")

    with pytest.raises(ValueError):
        pl.on_commands("bruh")


def test_matches():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_match(r"\d.\d")
    async def _(msg, ctx):
        await ctx.reply(ctx.match.group(0))

    @pl.on_match(r"(a|b|c).[a-z]")
    async def _(msg, ctx):
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

    @pl.on_any_message()
    async def _(msg, ctx):
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
    async def _(msg, ctx):
        await ctx.reply(msg.text)

    @pl.on_any_unprocessed_message()
    async def _(msg, ctx):
        await ctx.reply(msg.text * 2)

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".123", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".abc", (), 1, 0, 0, 0))
    assert hu(Update(None, UpdateType.UPD)) == hr.SKIPPED

    assert debug.answers[1][0] == (".123" * 2, (), {})
    assert debug.answers[1][1] == (".abc", (), {})


def test_commands():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_commands(["echo", "ec"])
    async def _(msg, ctx):
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


def test_attachments():
    app, debug, hu = make_kutana_no_run()

    pl = Plugin("")

    @pl.on_attachments(["image", "voice"])
    async def _(msg, ctx):
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


def test_plugins_multiple_hooks():
    pl = Plugin("")

    pl.on_start()(1)
    with pytest.raises(RuntimeError):
        pl.on_start()(1)

    pl.on_before()(1)
    with pytest.raises(RuntimeError):
        pl.on_before()(1)

    pl.on_after()(1)
    with pytest.raises(RuntimeError):
        pl.on_after()(1)

    pl.on_shutdown()(1)
    with pytest.raises(RuntimeError):
        pl.on_shutdown()(1)

    pl.on_exception()(1)
    with pytest.raises(RuntimeError):
        pl.on_exception()(1)
