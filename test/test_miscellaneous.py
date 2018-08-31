from kutana.controllers.vk import VKResponse
import kutana.plugins.norm.vk as vknorm
import unittest
import asyncio
import time


class TestMiscellaneous(unittest.TestCase):
    def test_vk_conversation(self):
        arguments = {}
        
        async def fake_resolveScreenName(*args, **kwargs):
            return VKResponse(False, "", "", {"object_id": 1}, "")
        
        resolveScreenName = vknorm.resolveScreenName
        vknorm.resolveScreenName = fake_resolveScreenName

        loop = asyncio.get_event_loop()

        loop.run_until_complete(
            vknorm.prepare(
                arguments,
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [], 
                "important": False, "peer_id": 1, 
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [], 
                "conversation_message_id": 1411, "out": 0, "from_id": 1, 
                "id": 0, "is_hidden": False}, "group_id": 1, 
                "type": "message_new"},
                {},
                {w: 1 for w in ("reply", "send_msg", "request", "upload_photo", "upload_doc")}
            )
        )

        self.assertEqual(arguments["message"].text, "echo  123")
        self.assertEqual(arguments["attachments"], ())

        loop.run_until_complete(
            vknorm.prepare(
                arguments,
                {"object": {"date": 1, "random_id": 0, "fwd_messages": [], 
                "important": False, "peer_id": 1, 
                "text": "echo [club1|\u0421\u043e] 123", "attachments": [], 
                "conversation_message_id": 1411, "out": 0, "from_id": 1, 
                "id": 0, "is_hidden": False}, "group_id": 2, 
                "type": "message_new"},
                {},
                {w: 1 for w in ("reply", "send_msg", "request", "upload_photo", "upload_doc")}
            )
        )

        self.assertEqual(arguments["message"].text, "echo [club1|\u0421\u043e] 123")
        self.assertEqual(arguments["attachments"], ())

        vknorm.resolveScreenName = resolveScreenName


if __name__ == '__main__':
    unittest.main()