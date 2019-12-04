import pytest
from kutana import (
    Plugin, Message, Update, UpdateType, Attachment, HandlerResponse as hr,
)
from testing_tools import make_kutana_no_run


# --------------------------------------- QUEST
pl = Plugin("Quest")


@pl.on_commands(["start"], user_state="")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:1")
    await ctx.reply("Choose: left or right")


@pl.on_commands(["left"], user_state="quest:1")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: left\nWrite '.ok'")


@pl.on_commands(["right"], user_state="quest:1")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: right\nWrite '.ok'")


@pl.on_commands(["ok"], user_state="quest:end")
async def _(msg, ctx):
    await ctx.set_state(user_state="")
    await ctx.reply("Bye")


@pl.on_any_unprocessed_message(user_state="quest:end")
async def _(msg, ctx):
    await ctx.reply("Write '.ok'")
# ---------------------------------------


def test_quest():
    app, debug, hu = make_kutana_no_run()

    app.add_plugin(pl)

    hu(Message(None, UpdateType.MSG, ".start", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".left", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".ok", (), 1, 0, 0, 0))
    assert debug.answers[1][-1] == ("Bye", (), {})

    hu(Message(None, UpdateType.MSG, ".start", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".start", (), 2, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".left", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".right", (), 2, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".ok", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".ok", (), 2, 0, 0, 0))
    assert debug.answers[1][-1] == ("Bye", (), {})
    assert debug.answers[2][-1] == ("Bye", (), {})

    hu(Message(None, UpdateType.MSG, ".left", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".right", (), 1, 0, 0, 0))
    assert debug.answers[1][-1] == ("Bye", (), {})

    hu(Message(None, UpdateType.MSG, ".start", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".left", (), 1, 0, 0, 0))
    hu(Message(None, UpdateType.MSG, ".bruh", (), 1, 0, 0, 0))
    assert debug.answers[1][-1] == ("Write '.ok'", (), {})
    hu(Message(None, UpdateType.MSG, ".ok", (), 1, 0, 0, 0))
    assert debug.answers[1][-1] == ("Bye", (), {})
    hu(Message(None, UpdateType.MSG, ".bruh", (), 1, 0, 0, 0))
    assert debug.answers[1][-1] == ("Bye", (), {})
