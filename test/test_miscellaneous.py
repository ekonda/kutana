from kutana import VKResponse, DebugController, Executor, load_plugins, \
    objdict, icedict, load_configuration
import kutana.controller_vk.converter as vk_converter
import unittest
import asyncio


class TestMiscellaneous(unittest.TestCase):
    def test_objdict(self):
        a = objdict()

        self.assertEqual(str(a), "{}")
        self.assertEqual(len(a), 0)
        self.assertEqual(list(i for i in a), [])

        a.a = 10  # pylint: disable=E0237
        self.assertEqual(a.a, 10)
        self.assertEqual(a["a"], 10)
        self.assertEqual(a.get("a"), 10)

        a["b"] = {"a": 5}
        self.assertEqual(a.b.a, 5)

        a["c"] = [1, 2]
        self.assertIs(a.c, a["c"])

        del a["a"]
        del a["b"]
        del a["c"]

        self.assertEqual(a, {})

    def test_icedict(self):
        a = icedict(a=10)

        self.assertEqual(str(a), "{'a': 10}")
        self.assertEqual(len(a), 1)
        self.assertEqual(list(i for i in a), ["a"])
        self.assertEqual(a["a"], 10)
        self.assertEqual(a.a, 10)

        b = icedict(a=10)

        self.assertEqual(a, b)
        self.assertEqual(a, {"a": 10})

        with self.assertRaises(TypeError):
            a["a"] = 10

    def test_functions(self):
        loaded_plugins = load_plugins("test/test_plugins/")

        self.assertEqual(len(loaded_plugins), 1)
        self.assertEqual(loaded_plugins[0].name, "Memory")

        executor = Executor()
        executor.register_plugins(*loaded_plugins)

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            executor(
                "message", objdict(
                    ctrl_type="debug",
                    convert_to_message=DebugController.convert_to_message
                )
            )
        )

        self.assertEqual(loaded_plugins[0].memory, "message")

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
