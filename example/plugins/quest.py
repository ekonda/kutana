from kutana import Plugin


pl = Plugin("Quest")


@pl.on_commands(["quest"], user_state="")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:1")
    await ctx.reply("Choose: left or right")


@pl.on_commands(["left"], user_state="quest:1")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:2")
    await ctx.reply("Choose: right or left")


@pl.on_commands(["left"], user_state="quest:2")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: left, left\nWrite '.OK'")


@pl.on_commands(["right"], user_state="quest:2")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: left, right\nWrite '.OK'")


@pl.on_commands(["right"], user_state="quest:1")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:3")
    await ctx.reply("Choose: right or left")


@pl.on_commands(["right"], user_state="quest:3")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: right, right\nWrite '.OK'")


@pl.on_commands(["left"], user_state="quest:3")
async def _(msg, ctx):
    await ctx.set_state(user_state="quest:end")
    await ctx.reply("You have chosen: right, left\nWrite '.OK'")


@pl.on_commands(["ok"], user_state="quest:end")
async def _(msg, ctx):
    await ctx.set_state(user_state="")
    await ctx.reply("Bye")


@pl.on_any_unprocessed_message(user_state="quest:end")
async def _(msg, ctx):
    await ctx.reply("Write '.OK'")


@pl.on_commands(["exit"])
async def _(msg, ctx):
    if ctx.user_state.startswith("quest:"):
        await ctx.set_state(user_state="")
        await ctx.reply("Quest stopped")


plugin = pl
