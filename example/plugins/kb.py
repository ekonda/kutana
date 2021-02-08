import json
from kutana import Plugin

plugin = Plugin("kb")


@plugin.vk.on_payloads([{"kind": "1"}])
async def __(msg, ctx):
    await ctx.reply(f"Handler for kind (1), your meta is '{ctx.payload['meta']}'")


@plugin.vk.on_payloads([{"kind": "2"}])
async def __(msg, ctx):
    await ctx.reply(f"Handler for kind (2), your meta is '{ctx.payload['meta']}'")


@plugin.on_commands(["kb"])
async def __(msg, ctx):
    await ctx.reply("hey", keyboard=json.dumps({
        "one_time": True,
        "buttons": [
            [
                {"action": {
                        "type":"text",
                        "label": "kind=1, meta=2", "payload": "{\"kind\": \"1\", \"meta\": \"2\"}"
                }}
            ],
            [
                {"action": {
                        "type":"text",
                        "label": "kind=1, meta=4", "payload": "{\"kind\": \"1\", \"meta\": \"4\"}"
                }}
            ],
            [
                {"action": {
                        "type":"text",
                        "label": "kind=2, meta=4", "payload": "{\"kind\": \"1\", \"meta\": \"4\"}"
                }}
            ],
        ]
    }))
