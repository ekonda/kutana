from test_framework import KutanaTest


class TestControllerDebug(KutanaTest):
    def test_plain(self):
        self.target = ["message"]

        with self.debug_controller([
                (1, "echo message"), (2, "echo message"), (2, "echo message"),
                (3, "echo message")
        ]) as plugin:
            async def on_echo(message, attachments, env):
                await env.reply(env.body)

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(
            self.controller.replies_others,
            {2: ["message", "message"], 3: ["message"]}
        )

    def test_empty_request(self):
        self.target = ["message"]

        with self.debug_controller(["echo message"]) as plugin:
            async def on_echo(message, attachments, env):
                self.assertIsNone(await env.request("users.get"))

                await env.reply(env.body)

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(self.controller.replies_others, {})
