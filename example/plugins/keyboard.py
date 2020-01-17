import json
from kutana import Plugin, HandlerResponse


# See https://vk.com/dev/bots_docs_3 for details
KEYBOARD_OBJECT = {
    "one_time": True,
    "buttons": [
        [
            {
                "action": {"type": "text", "payload": "1", "label": "One"},
                "color": "primary",
            },
            {
                "action": {"type": "text", "payload": "2", "label": "Two"},
                "color": "primary",
            },
        ],
        [
            {
                "action": {"type": "text", "payload": "3", "label": "Three"},
                "color": "primary",
            },
            {
                "action": {"type": "text", "payload": "4", "label": "Four"},
                "color": "primary",
            },
        ]
    ],
}


# Keyboard that will be send to VKONTAKTE is a STRING!
KEYBOARD_STRING = json.dumps(KEYBOARD_OBJECT)


# Plugins for sending keyboard.
plugin = Plugin(name="Keyboard", description="Keyboard for vkontakte")


@plugin.on_commands(["keyboard"])
async def _(msg, ctx):
    if ctx.backend.get_identity() != "vkontakte":
        await ctx.reply("This example works only for vk.com")
        return

    await ctx.reply("Message with keyboard", keyboard=KEYBOARD_STRING)


@plugin.vk.on_payload([1])
async def _(msg, ctx):
    await ctx.reply("Your choice was 1 (from handler)")


@plugin.vk.on_payload([2])
async def _(msg, ctx):
    await ctx.reply("Your choice was 2 (from handler)")


@plugin.vk.on_payload([3])
async def _(msg, ctx):
    await ctx.reply("Your choice was 3 (from handler)")


# This will never be called because of handler below
@plugin.vk.on_payload([4])
async def _(msg, ctx):
    await ctx.reply("Your choice was 4 (from handler)")


# Intercept all the messages with payloads and check their payload
@plugin.on_any_message(priority=10)
async def _(msg, ctx):
    # Only messages from vkontakte can have payload
    if ctx.backend.get_identity() != "vkontakte":
        return HandlerResponse.SKIPPED

    payload = msg.raw["object"]["message"].get("payload")

    if not payload or payload != "4":
        return HandlerResponse.SKIPPED

    await ctx.reply(
        "Your choice was 4 (from global interceptor)".format(payload)
    )
