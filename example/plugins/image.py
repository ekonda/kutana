from kutana import Plugin, Attachment, get_path


plugin = Plugin(name="Image", description="Send image")


@plugin.on_commands(["image"])
async def _(msg, ctx):
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        image = Attachment.new(fh.read(), "pizza.png")

    await ctx.reply("", attachments=image)
