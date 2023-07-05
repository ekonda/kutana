import time

from kutana import Plugin

plugin = Plugin(
    name="Waiter", description="Waits for you if you ask it to (.wait, .forget)"
)


WAITING = "waiter:waiting"


@plugin.on_commands(["wait"])
@plugin.with_storage(check_sender={"state": None})
async def _(msg, ctx):
    await ctx.sender.update_and_save({"state": WAITING, "waited_since": time.time()})
    await ctx.reply("Now I'm waiting!")


@plugin.on_commands(["wait"])
@plugin.with_storage(check_sender={"state": WAITING})
async def _(msg, ctx):
    waited_for = int(time.time() - ctx.sender["waited_since"])
    await ctx.reply(f"I'm already waiting for {waited_for} seconds!")


@plugin.on_commands(["forget"])
@plugin.with_storage()
async def _(msg, ctx):
    if ctx.sender.get("state") == WAITING:
        await ctx.sender.update_and_save({"state": None, "waited_since": None})
        await ctx.reply("Now I forgot you!")
    else:
        await ctx.reply("Who are you?")
