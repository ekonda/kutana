from kutana import Plugin, MemoryStorage


plugin = Plugin('Quest')


# Constants
PLAYING = 'quest:playing'
DONE = 'quest:done'
DATA = 'quest/data'


# Handlers
@plugin.on_commands(['quest'])
@plugin.expect_sender(state='')
async def __(msg, ctx):
    await ctx.sender.update({'state': PLAYING, DATA: []})
    await ctx.reply('You started your quest! Choose: ".1" or ".2".')


@plugin.on_commands(['1', '2'])
@plugin.expect_sender(state=PLAYING)
async def __(msg, ctx):
    if len(ctx.sender[DATA]) >= 2:
        await ctx.sender.update({'state': DONE, DATA: [*ctx.sender[DATA], ctx.command]})
        await ctx.reply('You chose 3 times! Type ".end" to see your results.')
        return

    await ctx.sender.update({'state': PLAYING, DATA: [*ctx.sender[DATA], ctx.command]})
    await ctx.reply(f'You chose {ctx.command}. Choose again!')


@plugin.on_commands(['end'])
@plugin.expect_sender(state=DONE)
async def __(msg, ctx):
    message = f'Your results: "{ctx.sender[DATA]}"'
    await ctx.sender.update({'state': ''}, remove=(DATA,))
    await ctx.reply(message)
