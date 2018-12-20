from kutana import VKResponse, DebugManager, Executor, load_plugins, \
    load_configuration
import kutana.manager.vk.converter as vk_converter
import unittest
import asyncio


class TestMiscellaneous(unittest.TestCase):
    def test_load_plugins(self):
        loaded_plugins = load_plugins("test/test_plugins/")

        self.assertEqual(len(loaded_plugins), 2)
        self.assertEqual(loaded_plugins[0].name, "Memory")
        self.assertEqual(loaded_plugins[1].name, "My file")

        executor = Executor()
        executor.register_plugins(*loaded_plugins)

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            executor(
                {
                    "kutana": self, "update_type": "startup",
                    "registered_plugins": executor.registered_plugins
                },
                {
                    "mngr_type": "kutana"
                }
            )
        )

        loop.run_until_complete(
            executor(
                "message", {
                    "mngr_type": "debug",
                    "convert_to_message": DebugManager.convert_to_message
                }
            )
        )

        self.assertEqual(loaded_plugins[0].memory, "message")
        self.assertEqual(loaded_plugins[1].my_file, ":)")

    def test_load_configuration(self):
        value = load_configuration("key", "test/test_assets/sample.json")

        self.assertEqual(value, "value")

        value = load_configuration("key2", "test/test_assets/sample.json")

        self.assertEqual(value, {"keynkey": "hvalue"})

    def test_vk_conversation(self):
        async def fake_resolveScreenName(*args, **kwargs):
            return VKResponse(False, (), {"object_id": 1})

        resolveScreenName = vk_converter.resolveScreenName
        vk_converter.resolveScreenName = fake_resolveScreenName

        loop = asyncio.get_event_loop()

        message = loop.run_until_complete(
            vk_converter.convert_to_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 1,
                "type": "message_new"},
                {w: 1 for w in ("reply", "send_msg", "request",
                "upload_photo", "upload_doc")}
            )
        )

        self.assertEqual(message.text, "echo  123")
        self.assertEqual(message.attachments, ())

        message = loop.run_until_complete(
            vk_converter.convert_to_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 2,
                "type": "message_new"},
                {w: 1 for w in ("reply", "send_msg", "request",
                "upload_photo", "upload_doc")}
            )
        )

        self.assertEqual(message.text, "echo [club1|\u0421\u043e] 123")
        self.assertEqual(message.attachments, ())

        vk_converter.resolveScreenName = resolveScreenName


if __name__ == '__main__':
    unittest.main()
