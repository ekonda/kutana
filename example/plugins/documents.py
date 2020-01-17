from kutana import Plugin, Attachment, get_path


plugin = Plugin(name="Documents", description="Send documents")


@plugin.on_commands(["documents"])
async def _(msg, ctx):
    # Document
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        doc = Attachment.new(fh.read(), "pizza.png")

    await ctx.reply("Document", attachments=doc)

    # Graffiti (special for vk)
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        graffiti = Attachment.new(fh.read(), "pizza.png", type="graffiti")

    try:
        await ctx.reply("Graffiti", attachments=graffiti)
    except ValueError:
        await ctx.reply("Can't upload this type of attachments")

    # Audio message
    with open(get_path(__file__, "assets/audio.ogg"), "rb") as fh:
        audio_message = Attachment.new(fh.read(), "audio.ogg", "voice")

    await ctx.reply("Audio message", attachments=audio_message)
