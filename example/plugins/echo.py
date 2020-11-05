from kutana import Plugin


plugin = Plugin(name="Echo", description="Reply with send message")


@plugin.on_commands(["echo"])
async def __(msg, ctx):
    await ctx.reply("{}".format(ctx.body or '(/)'), attachments=msg.attachments)
