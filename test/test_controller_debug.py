from test_framework import KutanaTest


class TestManagerDebug(KutanaTest):
    def test_plain(self):
        self.target = ["message"]

        with self.debug_manager(["echo message"]) as plugin:
            async def on_echo(message, attachments, env):
                self.assertIsNone(await env["request"]("users.get"))

                await env["reply"](env["body"])

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(self.manager.replies_all, {1: ["message"]})

    def test_multiple_senders_plain(self):
        self.target = ["message"]

        with self.debug_manager([
                (1, "echo message"), (2, "echo message"), (2, "echo message"),
                (3, "echo message")
        ]) as plugin:
            async def on_echo(message, attachments, env):
                await env["reply"](env["body"])

            plugin.on_startswith_text("echo")(on_echo)

        self.assertEqual(
            self.manager.replies_all,
            {1: ["message"], 2: ["message", "message"], 3: ["message"]}
        )
