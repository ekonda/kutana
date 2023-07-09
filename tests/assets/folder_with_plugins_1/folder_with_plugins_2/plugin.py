from kutana import Plugin

plugin = Plugin("plugin 1")


@plugin.on_commands(["hi", "hello"])
async def _(ctx, msg):
    await ctx.reply("hello")


@plugin.on_match(["bad ?word"])
async def _(ctx, msg):
    await ctx.reply("don't swear!")
