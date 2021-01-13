import time
from kutana import Plugin, t


plugin = Plugin(t("Waiter"), description=t("Waits for you if you ask it to (.wait, .forget)"))


WAITING = "waiter:waiting"


@plugin.on_commands(["wait"])
@plugin.expect_sender(state="")
async def __(msg, ctx):
    await ctx.sender.update({"state": WAITING, "waited_since": time.time()})
    await ctx.reply(t("Now I'm waiting!"))


@plugin.on_commands(["wait"])
@plugin.expect_sender(state=WAITING)
async def __(msg, ctx):
    waited_for = int(time.time() - ctx.sender["waited_since"])
    await ctx.reply(t("I'm already waiting for {} seconds!", waited_for, num=waited_for))


@plugin.on_commands(["forget"])
@plugin.expect_sender()
async def __(msg, ctx):
    if ctx.sender["state"] == WAITING:
        await ctx.sender.update({"state": ""}, remove=['waited_since'])
        await ctx.reply(t("Now I forgot you!"))
    else:
        await ctx.reply(t("Who are you?"))
