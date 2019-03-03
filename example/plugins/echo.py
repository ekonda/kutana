from kutana import Plugin


plugin = Plugin(name="Echo")


@plugin.on_startswith_text("echo")
async def on_echo(message, env, body):
    await env.reply("{}".format(body), attachment=message.attachments)
