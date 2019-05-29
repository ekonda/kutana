from testing_tools import KutanaTest


class TestManagerDebug(KutanaTest):
    def test_plain(self):
        self.target = ["message"]

        with self.debug_manager(["echo message"]) as plugin:

            @plugin.on_startswith_text("echo")
            async def _(message, env):
                await env.reply(env.body)

        self.assertEqual(self.manager.replies_all, {1: ["message"]})

    def test_request(self):
        with self.debug_manager(["echo message"]) as plugin:

            @plugin.on_startswith_text("echo")
            async def _(message, env):
                self.assertEqual(await env.request("method"), None)


    def test_upload_photo(self):
        with self.debug_manager(["132"]) as plugin:

            @plugin.on_has_text()
            async def _(message, env):
                attachment = await env.upload_photo("photo")

                self.assertEqual("photo", attachment)
                self.assertEqual(
                    "photo", await env.get_file_from_attachment(attachment)
                )

    def test_send_message(self):
        self.target = ["message"]

        with self.debug_manager(["echo message"]) as plugin:

            @plugin.on_startswith_text("echo")
            async def _(message, env):
                await env.send_message(env.body, 1)

    def test_multiple_senders_plain(self):
        self.target = ["message1"]

        with self.debug_manager([
            (1, "echo message1"),
            (2, "echo message2"),
            (2, "echo message3"),
            (3, "echo message4")
        ]) as plugin:

            @plugin.on_startswith_text("echo")
            async def _(message, env):
                await env.reply(env.body)

        self.assertEqual(
            self.manager.replies_all,
            {1: ["message1"], 2: ["message2", "message3"], 3: ["message4"]}
        )
