from kutana import Plugin, get_path


plugin = Plugin(name="Documents", description="Send documents")


@plugin.on_text("documents")
async def _(message, env):
    # Document
    with open(get_path(__file__, "document_assets/pizza.png"), "rb") as fh:
        doc = await env.upload_doc(fh.read(), filename="pizza.png")

    await env.reply("Document", attachment=doc)

    # Graffiti
    with open(get_path(__file__, "document_assets/pizza.png"), "rb") as fh:
        graffiti = await env.upload_doc(fh.read(), type="graffiti", filename="pizza.png")

    await env.reply("Graffiti", attachment=graffiti)

    # Audio message
    with open(get_path(__file__, "document_assets/audio.mp3"), "rb") as fh:
        audio_message = await env.upload_doc(fh.read(), type="audio_message", filename="audio.mp3")

    await env.reply("Audio message", attachment=audio_message)
