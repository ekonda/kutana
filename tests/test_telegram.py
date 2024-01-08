import asyncio
import json
import logging

from kutana import Kutana, Plugin
from kutana.backends import Telegram
from kutana.update import Attachment, AttachmentKind

# Load updates for simulating requests to telegram
with open("tests/test_telegram.json", "r") as fh:
    TELEGRAM_DATA = json.load(fh)

# Create some plugins for tests
plugin1 = Plugin("echo")


@plugin1.on_commands(["echo"])
async def _(upd, ctx):
    await ctx.reply(upd.text)


plugin2 = Plugin("image")


@plugin2.on_attachments([AttachmentKind.IMAGE])
async def _(upd, ctx):
    await ctx.reply(
        upd.text,
        attachments=[
            *upd.attachments,
            Attachment(kind=AttachmentKind.AUDIO, content=("song.mp3", "123")),
            Attachment(kind=AttachmentKind.VIDEO, content=("video.mp4", "123")),
            Attachment(kind=AttachmentKind.DOCUMENT, content=("file.pdf", "123")),
            Attachment(kind=AttachmentKind.VOICE, content=("voice.ogg", "123")),
        ],
    )


# Test
async def test_telegram():
    backend = Telegram("nicetoken")

    normalized_requests = []

    async def _request(method, kwargs):
        await asyncio.sleep(0)

        for mock in TELEGRAM_DATA:
            if mock["method"] == method and mock["kwargs"] == json.loads(json.dumps(kwargs)):
                normalized_requests.append((mock["method"], mock["kwargs"]))
                return mock["response"]

        logging.critical('Unexpected request: "%s" "%s"', method, kwargs)

    backend.request = _request

    # Special plugin for stopping test application
    stopper_plugin = Plugin("_stopper", updates_processed=0)

    def _update_processed():
        stopper_plugin.updates_processed += 1
        if stopper_plugin.updates_processed >= 3:
            future.cancel()

    @stopper_plugin.on_completion()
    async def _(context):
        _update_processed()

    @stopper_plugin.on_exception()
    async def _(context, exception):
        _update_processed()

    # create application, fill it with plugins and backends
    app = Kutana()

    app.add_backend(backend)

    app.add_plugin(stopper_plugin)
    app.add_plugin(plugin1)
    app.add_plugin(plugin2)

    # run application (save to variable for stopper)
    future = asyncio.ensure_future(app._run_wrapper())

    try:
        await future
    except asyncio.CancelledError:
        pass
    finally:
        await app._shutdown_wrapper()

    # Assert all the needed requests were made
    assert ("sendMessage", {"chat_id": 123123123, "text": "/echo"}) in normalized_requests
    assert ("sendMessage", {"chat_id": 123123123, "text": "/echo @shiudfhjkads_bot"}) in normalized_requests
    assert (
        "sendPhoto",
        {"chat_id": 123123123, "photo": "gfhSDFSDFSDFfhjgfjdghffkhjgfhjtfjkghfhjgfGHFGDHFGDGFDHHFjtg"},
    ) in normalized_requests
    assert ("sendAudio", {"chat_id": 123123123, "audio": ["song.mp3", "123"], "caption": "song.mp3"}) in normalized_requests
    assert ("sendVideo", {"chat_id": 123123123, "video": ["video.mp4", "123"], "caption": "video.mp4"}) in normalized_requests
    assert ("sendDocument", {"chat_id": 123123123, "document": ["file.pdf", "123"], "caption": "file.pdf"}) in normalized_requests
    assert ("sendVoice", {"chat_id": 123123123, "voice": ["voice.ogg", "123"], "caption": "voice.ogg"}) in normalized_requests
