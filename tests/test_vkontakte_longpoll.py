import asyncio
import json
import logging

import httpx

from kutana import Kutana, Plugin
from kutana.backends.vkontakte import VkontakteLongpoll
from kutana.update import Attachment, AttachmentKind

# Load updates for simulating requests to telegram
with open("tests/test_vkontakte_longpoll.json", "r") as fh:
    VKONTAKTE_LONGPOLL_DATA = json.load(fh)

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


class MockedAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requests = []

    async def request(self, method, url, params=None, **kwargs):
        await asyncio.sleep(0)

        for mock in VKONTAKTE_LONGPOLL_DATA:
            if not url.startswith(mock["url"]):
                continue

            if mock["params"] and params != mock["params"]:
                continue

            self.requests.append((mock["url"], mock["params"]))

            return httpx.Response(200, content=json.dumps(mock["response"]))

        logging.critical('Unexpected request: "%s" "%s"', method, kwargs)

        return httpx.Response(500, content="null")


# Test
async def test_vkontakte_longpoll():
    backend = VkontakteLongpoll("nicetoken")
    client = MockedAsyncClient()
    backend.client = client

    # Special plugin for stopping test application
    stopper_plugin = Plugin("_stopper", updates_processed=0)

    def _update_processed():
        stopper_plugin.updates_processed += 1
        if stopper_plugin.updates_processed >= 0:
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
    future = asyncio.ensure_future(app._run())

    try:
        await future
    except asyncio.CancelledError:
        pass
    finally:
        await app._shutdown_wrapper()

    # Assert all the needed requests were made
    assert ("https://api.vk.com/method/groups.getById", {"fields": "screen_name"}) in client.requests
    assert ("https://lp.vk.com/wh654327632?act=a_check&key=123123123&wait=25&ts=1", {}) in client.requests
    assert ("https://api.vk.com/method/execute", None) in client.requests
