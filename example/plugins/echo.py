from kutana import Plugin, t


plugin = Plugin(name=t("Echo"), description=t("Sends your messages back (.echo)"))


@plugin.on_commands(["echo"])
async def __(msg, ctx):
    await ctx.reply("{}".format(ctx.body or '(/)'), attachments=msg.attachments, disable_mentions=0)
