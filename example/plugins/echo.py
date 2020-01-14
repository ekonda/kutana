from kutana import Plugin


plugin = Plugin(name="Echo", description="Reply with send message")


@plugin.on_commands(["echo"])
async def _(msg, ctx):
    await ctx.reply("{}".format(ctx.body), attachments=msg.attachments)
