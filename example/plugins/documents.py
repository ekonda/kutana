from kutana import Plugin, Attachment, get_path, t


plugin = Plugin(name=t("Attachments"), description=t("Sends some attachments (.attachments)"))


@plugin.on_commands(["attachments"])
async def __(msg, ctx):
    # Image
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        image = Attachment.new(fh.read(), "pizza.png")

    await ctx.reply(t("Image"), attachments=image)

    # Document
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        doc = Attachment.new(fh.read(), "pizza.png")

    await ctx.reply(t("Document"), attachments=doc)

    # Audio message
    with open(get_path(__file__, "assets/audio.ogg"), "rb") as fh:
        audio_message = Attachment.new(fh.read(), "audio.ogg", "voice")

    await ctx.reply(t("Audio message"), attachments=audio_message)
