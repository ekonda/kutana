from kutana import Plugin

plugin = Plugin()

plugin.name = "Echo"

@plugin.on_startswith_text("echo")
async def on_message(message, attachments, env, extenv):
    a_image = await env.upload_photo("test/author.png")
    a_doc = await env.upload_doc("test/girl.ogg", doctype="audio_message", filename="file.ogg")

    await env.reply("{}!".format(env.body), attachment=(a_image, a_doc))