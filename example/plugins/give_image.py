from kutana import Plugin, MemoryStorage


plugin = Plugin("Give image")


# Constants
WAITING_STATE = "give_image:waiting"


# Handlers
@plugin.on_commands(["give_image", "giveimage"])
@plugin.expect_sender(state="")
async def __(msg, ctx):
    if msg.attachments:
        await ctx.reply("You image:", attachments=msg.attachments[0])
        return

    await ctx.sender.update({"state": WAITING_STATE})
    await ctx.reply("Please, send you image")


@plugin.on_attachments(["image"])
@plugin.expect_sender(state=WAITING_STATE)
async def __(msg, ctx):
    await ctx.sender.update({"state": ""})
    await ctx.reply("You image:", attachments=msg.attachments[0])


@plugin.on_unprocessed_messages()
@plugin.expect_sender(state=WAITING_STATE)
async def __(msg, ctx):
    await ctx.sender.update({"state": ""})
    await ctx.reply("Expected to see image from you!")
