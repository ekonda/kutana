from kutana import Plugin

plugin = Plugin(name="Grand echo")

@plugin.on_startswith_text("echo")
async def on_echo(message, attachments, env):
    a_image = await env.upload_photo("test/test_assets/author.png")
    a_doc = await env.upload_doc("test/test_assets/girl.ogg", doctype="audio_message", filename="file.ogg")

    await env.reply("{}!".format(env.body), attachment=(a_image, a_doc))
