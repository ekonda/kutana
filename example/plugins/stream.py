import asyncio
from kutana import Plugin, Attachment, get_path, RequestException


# This example shows how to access existing backend instance and perform
# some actions outside of handlers.


plugin = Plugin(name="Stream", description="Send images to subscribers")


subscribers = []


async def bg_loop(vk):
    while True:
        with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
            temp_a = Attachment.new(fh.read(), "pizza.png")

        try:
            a = await vk.upload_attachment(temp_a, peer_id=None)
        except RequestException:
            for sub in subscribers:
                await vk.send_message(sub, "Failed to upload attachment; Paused for 1 hour")

            await asyncio.sleep(60 * 60)

            continue

        for sub in subscribers:
            await vk.send_message(sub, "", a)

        await asyncio.sleep(60 * 10)

@plugin.on_start()
async def _(app):
    backend = app.get_backends()[0]

    # Run only if first backend is Vkontakte
    if backend.get_identity() == "vkontakte":
        asyncio.ensure_future(bg_loop(backend))

@plugin.on_commands(["stream sub"])
async def _(msg, ctx):
    subscribers.append(msg.receiver_id)
    await ctx.reply("OK")


@plugin.on_commands(["stream unsub"])
async def _(msg, ctx):
    subscribers.remove(msg.receiver_id)
    await ctx.reply("OK")
