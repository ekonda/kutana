import pytest

from kutana.backends.debug import Debug
from kutana.plugin import Plugin
from kutana.update import Attachment, AttachmentKind


def test_attributes():
    plugin = Plugin("plugin", a=1, b=2)
    plugin.c = 3
    assert plugin.a == 1
    assert plugin.b == 2
    assert plugin.c == 3


def test_unknown_attribute():
    pl = Plugin("plugin")

    with pytest.raises(AttributeError):
        pl.bruh


async def test_on_messages():
    pl = Plugin("plugin")

    @pl.on_messages()
    async def _(upd, ctx):
        await ctx.reply("hey")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("/hey", 1, 9001, []),
            ("/nothey", 1, 9001, []),
            ("/hey", 1, 9001, []),
        ],
    )  # type: ignore

    assert backend.messages == [
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
    ]


async def test_on_commands():
    pl = Plugin("plugin")

    @pl.on_commands(["hey"])
    async def _(upd, ctx):
        await ctx.reply("hey")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("/hey", 1, 9001, []),
            ("/nothey", 1, 9001, []),
            ("/hey", 1, 9001, []),
        ],
    )  # type: ignore

    assert backend.messages == [
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
    ]


async def test_on_match():
    pl = Plugin("plugin")

    @pl.on_match([r"^hey(\d)?$"])
    async def _(upd, ctx):
        await ctx.reply(f"yeah, {ctx.match.group(1)}")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("hey", 1, 9001, []),
            ("hey10", 1, 9001, []),
            ("hey5", 1, 9001, []),
        ],
    )  # type: ignore

    assert backend.messages == [
        (9001, "yeah, None", None, {}),
        (9001, "yeah, 5", None, {}),
    ]


async def test_on_updates():
    pl = Plugin("plugin")

    @pl.on_updates()
    async def _(upd, ctx):
        await ctx.reply("hey")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("/hey", 1, 9001, []),
            ("/nothey", 1, 9001, []),
            ("/hey", 1, 9001, []),
        ],
    )  # type: ignore

    assert backend.messages == [
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
    ]


async def test_on_attachments():
    pl = Plugin("plugin")

    @pl.on_attachments([AttachmentKind.IMAGE])
    async def _(upd, ctx):
        await ctx.reply("hey")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("/hey", 1, 9001, [Attachment(id=1, kind=AttachmentKind.IMAGE)]),
            ("/nothey", 1, 9001, [Attachment(id=1, kind=AttachmentKind.IMAGE)]),
            ("/hey", 1, 9001, [Attachment(id=3, kind=AttachmentKind.VOICE)]),
        ],
    )  # type: ignore

    assert backend.messages == [
        (9001, "hey", None, {}),
        (9001, "hey", None, {}),
    ]


async def test_event_hooks():
    pl = Plugin("plugin")

    called_on_start = False
    called_on_exception = False
    called_on_completion = False
    called_on_shutdown = False

    @pl.on_start()
    async def _():
        nonlocal called_on_start
        called_on_start = True

    @pl.on_completion()
    async def _(ctx):
        nonlocal called_on_completion
        called_on_completion = True

    @pl.on_exception()
    async def _(ctx, exc):
        nonlocal called_on_exception
        called_on_exception = True

    @pl.on_shutdown()
    async def _():
        nonlocal called_on_shutdown
        called_on_shutdown = True

    @pl.on_commands(["/fail"])
    async def _(ctx, exc):
        raise RuntimeError("Oops")

    _, backend = await Debug.handle_updates(
        [pl],
        [
            ("/hey", 1, 9001, []),
            ("/fail", 1, 9001, []),
        ],
    )  # type: ignore

    assert called_on_start
    assert called_on_completion
    assert called_on_exception
    assert called_on_shutdown
    assert backend.messages == []
