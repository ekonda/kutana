from kutana import Kutana, VKManager, ExitException, Plugin, Attachment
from kutana.manager.vk.environment import VKEnvironment
import unittest
import requests
import logging
import asyncio
import time
import json
import os


class TestManagerVk(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        logging.disable(logging.INFO)

    def tearDown(self):
        logging.disable(logging.DEBUG)

    def test_vk_exceptions(self):
        with self.assertRaises(ValueError):
            VKManager("")

    def test_vk_no_peer_id(self):
        env = VKEnvironment(VKManager("token"), None)

        res = self.loop.run_until_complete(
            env.reply("message")
        )

        self.assertEqual(res, ())

    def test_vk_manager_raw_request(self):
        mngr = VKManager("token")

        response = self.loop.run_until_complete(
            mngr.raw_request("any.method", a1="v1", a2="v2")
        )

        self.assertEqual(response.errors[0][1]["error_code"], 5)

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_vk_manager_request(self):
        mngr = VKManager("token")

        response = self.loop.run_until_complete(
            mngr.request("fake.method", _timeout=0)
        )

        self.assertTrue(response.error)
        self.assertEqual(len(mngr.requests_queue), 1)
        self.assertEqual(mngr.requests_queue[0].method, "fake.method")
        self.assertEqual(mngr.requests_queue[0].kwargs, {})

    def test_vk_manager_send_message(self):
        mngr = VKManager("token")

        responses = self.loop.run_until_complete(
            mngr.send_message("text for message", 0, ["attachment"], _timeout=0)
        )

        response = responses[0]

        self.assertTrue(response.error)
        self.assertEqual(len(mngr.requests_queue), 1)
        self.assertEqual(mngr.requests_queue[0].method, "messages.send")
        self.assertEqual(mngr.requests_queue[0].kwargs, {
            "message": "text for message",
            "attachment": "attachment,",
            "peer_id": 0
        })

    def test_vk_manager_send_message_attachment(self):
        mngr = VKManager("token")

        attachment = Attachment("photo", 1, 0, None, None, None)

        responses = self.loop.run_until_complete(
            mngr.send_message("text for message", 0, attachment, _timeout=0)
        )

        response = responses[0]

        self.assertTrue(response.error)
        self.assertEqual(len(mngr.requests_queue), 1)
        self.assertEqual(mngr.requests_queue[0].method, "messages.send")
        self.assertEqual(mngr.requests_queue[0].kwargs, {
            "message": "text for message",
            "attachment": "photo0_1,",
            "peer_id": 0
        })

    def test_vk_manager_convert_to_attachment(self):
        test_attachment_raw = {
            "id": 13, "album_id": 13, "owner_id": 1, "sizes":
            [{"type": "s", "url": "url", "width": 0, "height": 0}],
            "text": "", "date": 0, "post_id": 0, "likes":
            {"user_likes": 0, "count": 577904}, "comments": {"count": 421},
            "can_comment": 1, "can_repost": 1, "tags": {"count": 0}
        }

        attachment = VKManager.convert_to_attachment(
            test_attachment_raw, "photo"
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "photo")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_convert_to_attachment_no_type(self):
        test_attachment_raw = {
            "type": "photo",
            "photo": {
                "id": 13, "album_id": 13, "owner_id": 1, "sizes":
                [{"type": "s", "url": "url2", "width": 0, "height": 0},
                {"type": "m", "url": "url", "width": 0, "height": 0}],
                "text": "", "date": 0, "post_id": 0, "likes":
                {"user_likes": 0, "count": 577904}, "comments": {"count": 421},
                "can_comment": 1, "can_repost": 1, "tags": {"count": 0}
            }
        }

        attachment = VKManager.convert_to_attachment(
            test_attachment_raw
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "photo")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_convert_to_attachment_doc(self):
        test_attachment_raw = {
            "id": 13, "owner_id": 1, "title": "rrrrr.png", "size": 119900,
            "ext": "png", "url": "url", "date": 0, "type": 4,
        }

        attachment = VKManager.convert_to_attachment(
            test_attachment_raw, "doc"
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "doc")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_convert_to_attachment_doc_no_link(self):
        test_attachment_raw = {
            "id": 13, "owner_id": 1, "title": "rrrrr.png", "size": 119900,
            "ext": "png", "date": 0, "type": 4,
        }

        attachment = VKManager.convert_to_attachment(
            test_attachment_raw, "doc"
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "doc")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, None)
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)
