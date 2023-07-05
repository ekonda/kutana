from kutana import Attachment, Plugin, get_path
from kutana.update import AttachmentKind

plugin = Plugin(name="Attachments", description="Sends some attachments (.attachments)")


@plugin.on_commands(["attachments"])
async def _(msg, ctx):
    # Image
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        image = Attachment(
            kind=AttachmentKind.IMAGE,
            content=("pizza.png", fh.read()),
        )

    await ctx.reply("Image", attachments=[image])

    # Document
    with open(get_path(__file__, "assets/pizza.png"), "rb") as fh:
        doc = Attachment(
            kind=AttachmentKind.DOCUMENT,
            content=("pizza.png", fh.read()),
            title="Pizza",
        )

    await ctx.reply("Document", attachments=[doc])

    # Audio message
    with open(get_path(__file__, "assets/audio.ogg"), "rb") as fh:
        audio_message = Attachment(
            kind=AttachmentKind.VOICE,
            content=("audio.ogg", fh.read()),
        )

    await ctx.reply("Audio message", attachments=[audio_message])
