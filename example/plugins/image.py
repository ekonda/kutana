from kutana import Plugin, get_path


plugin = Plugin(name="Image", description="Send image")


@plugin.on_text("image")
async def _(message, env):
    with open(get_path(__file__, "send_image_assets/pizza.png"), "rb") as fh:
        image = await env.upload_photo(fh.read())

    await env.reply("", attachment=image)
