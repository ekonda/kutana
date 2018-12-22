from kutana import VKResponse, VKEnvironment, DebugEnvironment, DebugManager, \
    Executor, load_plugins, load_configuration, VKManager
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

        loop.run_until_complete(executor.startup(None))

        loop.run_until_complete(
            executor("message",
                DebugEnvironment(
                    DebugManager(), peer_id=0
                )
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
        class FakeManager(VKManager):
            def __init__(self):
                pass

            async def request(self, *args, **kwargs):
                return VKResponse(False, (), {"object_id": 1})

        env = VKEnvironment(FakeManager(), peer_id=0)

        loop = asyncio.get_event_loop()

        message = loop.run_until_complete(
            env.convert_to_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 1,
                "type": "message_new"}
            )
        )

        self.assertEqual(message.text, "echo  123")
        self.assertEqual(message.attachments, ())

        message = loop.run_until_complete(
            env.convert_to_message(
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [],
                "important": False, "peer_id": 1,
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [],
                "conversation_message_id": 1411, "out": 0, "from_id": 1,
                "id": 0, "is_hidden": False}, "group_id": 2,
                "type": "message_new"}
            )
        )

        self.assertEqual(message.text, "echo [club1|\u0421\u043e] 123")
        self.assertEqual(message.attachments, ())


if __name__ == '__main__':
    unittest.main()
