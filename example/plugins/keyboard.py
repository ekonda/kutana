import json

from kutana import Plugin, get_path


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
plugin1 = Plugin(name="Keyboard", description="Keyboard for vkontakte")


@plugin1.on_text("keyboard")
async def _(message, env):
    if env.manager_type != "vkontakte":
        await env.reply("This example works only for vk.com")
        return

    await env.reply("Keyboard", keyboard=KEYBOARD_STRING)


# Plugin for intercepting messages with payload.
plugin2 = Plugin(name="_Keyboard_listener", priority=10)


@plugin2.on_has_text()
async def _(message, env):
    payload = message.raw_update["object"].get("payload")

    if not payload:
        return "GOON"

    await env.reply('Your choice was: "{}"'.format(payload))


plugins = [plugin1, plugin2]
