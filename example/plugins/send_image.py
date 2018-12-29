from kutana import Plugin, get_path


plugin = Plugin(name="Show me")


@plugin.on_text("showme")
async def on_echo(message, env):
    with open(get_path(__file__, "send_image_assets/pizza.png"), "rb") as fh:
        image = await env.upload_photo(fh.read())

    await env.reply("", attachment=image)
