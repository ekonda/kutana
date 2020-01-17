import asyncio
from kutana import Plugin, Attachment, get_path


# This example shows how to access existing backend instance and perform
# some actions outside of handlers.


plugin = Plugin(name="Stream", description="Send images to subscribers")


subscribers = []


async def bg_loop(vk):
    while True:
        with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
            temp_a = Attachment.new(fh.read(), "pizza.png")

        a = await vk.upload_attachment(temp_a, peer_id=None)

        for sub in subscribers:
            await vk.send_message(sub, "", a)

        await asyncio.sleep(5)

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
