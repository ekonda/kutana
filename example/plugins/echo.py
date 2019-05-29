from kutana import Plugin


plugin = Plugin(name="Echo", description="Reply with send message")


@plugin.on_startswith_text("echo")
async def _(message, env):
    await env.reply("{}".format(env.body), attachment=message.attachments)
