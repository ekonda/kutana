from kutana.backends.debug import Debug
from kutana.plugin import Plugin


async def test_vk_on_payloads():
    pl = Plugin("plugin")

    @pl.vk.on_payloads([{"m": 1}])
    @pl.vk.on_payloads([{"m": 3}])
    async def _(upd, ctx):
        await ctx.reply(ctx.payload["m"])

    _, backend = await Debug.handle_updates(
        [pl],
        [
            (
                "/hey",
                1,
                9001,
                [],
                {"object": {"message": {"payload": '{"m": 1}'}}},
            ),
            (
                "/hey",
                1,
                9001,
                [],
                {"object": {"message": {"payload": '{"m": 2}'}}},
            ),
            (
                "/hey",
                1,
                9001,
                [],
                {"object": {"message": {"payload": '{"m": 3}'}}},
            ),
            (
                "/hey",
                1,
                9001,
                [],
                {"object": {"message": {"payload": '{"m": 3, "n": 10}'}}},
            ),
        ],
        identity="vk",
    )  # type: ignore

    assert backend.messages == [
        (9001, "1", None, {}),
        (9001, "3", None, {}),
        (9001, "3", None, {}),
    ]


async def test_vk_on_chat_actions():
    pl = Plugin("plugin")

    @pl.vk.on_chat_actions(["chat_title_update"])
    async def _(upd, ctx):
        await ctx.reply(ctx.chat_action["text"])

    _, backend = await Debug.handle_updates(
        [pl],
        [
            (
                "/hey",
                1,
                9001,
                [],
                {
                    "object": {
                        "message": {
                            "action": {
                                "type": "chat_title_update",
                                "text": "hey",
                            },
                        },
                    },
                },
            ),
            (
                "/hey",
                1,
                9001,
                [],
                {
                    "object": {
                        "message": {
                            "action": {
                                "type": "chat_invite_user",
                            },
                        },
                    },
                },
            ),
        ],
        identity="vk",
    )  # type: ignore

    assert backend.messages == [
        (9001, "hey", None, {}),
    ]
