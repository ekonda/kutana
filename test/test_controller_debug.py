from test_framework import KutanaTest


class TestManagerDebug(KutanaTest):
    def test_plain(self):
        self.target = ["message"]

        with self.debug_manager(["echo message"]) as plugin:

            async def on_echo(message, env):
                self.assertIsNone(await env.request("users.get"))
                await env.reply(env.meta["body"])

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(self.manager.replies_all, {1: ["message"]})

    def test_multiple_senders_plain(self):
        self.target = ["message1"]

        with self.debug_manager([
                (1, "echo message1"),
                (2, "echo message2"),
                (2, "echo message3"),
                (3, "echo message4")
        ]) as plugin:

            async def on_echo(message, env):
                await env.reply(env.meta["body"])

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(
            self.manager.replies_all,
            {1: ["message1"], 2: ["message2", "message3"], 3: ["message4"]}
        )
