from kutana import Plugin

plugin1 = Plugin("hello 1")

@plugin1.on_match("hello1")
async def __(message, ctx):
    await ctx.reply("hi1")

plugin2 = Plugin("hello 2")

@plugin2.on_match("hello2")
async def __(message, ctx):
    await ctx.reply("hi2")

plugins = [plugin1, plugin2]
