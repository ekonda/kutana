from kutana import Plugin

plugin = Plugin("echo")

@plugin.on_commands(["echo", "ec"])
async def __(message, ctx):
    await ctx.reply(ctx.route["args"])
