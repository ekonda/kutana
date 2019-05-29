from kutana import Plugin, get_path


plugin = Plugin(name="Document", description="Send document")


@plugin.on_text("document")
async def _(message, env):
    with open(get_path(__file__, "send_image_assets/pizza.png"), "rb") as fh:
        doc = await env.upload_doc(fh.read(), filename="pizza.png")

    await env.reply("", attachment=doc)
