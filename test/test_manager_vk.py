import asyncio
import json
import logging
import os
import time
import types
import unittest

import aiohttp
import requests
from kutana import (Attachment, ExitException, Kutana, Plugin, VKManager,
                    VKResponse, VKRequest, VKEnvironment)


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

    def test_vk_get_background_coroutines(self):
        mngr = VKManager("token")

        bg_coroutines = self.loop.run_until_complete(
            mngr.get_background_coroutines(asyncio.ensure_future)
        )

        mngr.running = False

        self.loop.run_until_complete(bg_coroutines[0])

        self.assertEqual(len(bg_coroutines), 1)

    def test_vk_environment(self):
        mngr = VKManager("token")
        env = self.loop.run_until_complete(
            mngr.get_environment({"object": {"peer_id": 1}})
        )

        self.assertEqual(env.peer_id, 1)
        self.assertEqual(env.manager, mngr)

    def test_vk_update_longpoll_data(self):
        mngr = VKManager("token")

        async def raw_request(self, method, **kwargs):
            return VKResponse(
                False, (), {"key": "key", "server": "server", "ts": "0"}
            )

        mngr.raw_request = types.MethodType(raw_request, mngr)

        self.loop.run_until_complete(
            mngr.update_longpoll_data()
        )

        self.loop.run_until_complete(
            mngr.dispose()
        )

        self.assertEqual(
            mngr.longpoll,
            {"key": "key", "server": "server", "ts": "0"}
        )

    def test_vk_update_longpoll_data_exception(self):
        mngr = VKManager("token")

        async def raw_request(self, method, **kwargs):
            return VKResponse(True, (), "")

        mngr.raw_request = types.MethodType(raw_request, mngr)

        with self.assertRaises(ValueError):
            self.loop.run_until_complete(
                mngr.update_longpoll_data()
            )

        self.loop.run_until_complete(
            mngr.dispose()
        )

        self.assertEqual(mngr.longpoll, None)

    def test_vk_receiver(self):
        mngr = VKManager("token")

        async def prepare():
            mngr.longpoll = {
                "ts": 0, "server": "server", "key": "key"
            }

            mngr.session = aiohttp.ClientSession()

            class FakePost:
                def __init__(self, url):
                    pass

                async def __aenter__(self):
                    class FakeResponse:
                        async def json(self):
                            return {
                                "ts": "4",
                                "updates": [
                                    {"type": "type", "object": "object"},
                                    "update2"
                                ]
                            }

                    return FakeResponse()

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            def post(self, url):
                return FakePost(url)

            mngr.session.post = types.MethodType(post, mngr.session)

        self.loop.run_until_complete(prepare())

        updates = self.loop.run_until_complete(mngr.receiver())

        self.assertEqual(updates, [{"type": "type", "object": "object"}])
        self.assertEqual(mngr.longpoll["ts"], "4")

        self.loop.run_until_complete(mngr.dispose())


    def test_vk_receiver_failed(self):
        mngr = VKManager("token")

        async def prepare():
            mngr.longpoll = {
                "ts": 0, "server": "server", "key": "key"
            }

            mngr.session = aiohttp.ClientSession()

            class FakePost:
                def __init__(self, url):
                    pass

                async def __aenter__(self):
                    class FakeResponse:
                        async def json(self):
                            return {"failed": 2}

                    return FakeResponse()

                async def __aexit__(self, exc_type, exc, tb):
                    pass

            def post(self, url):
                return FakePost(url)

            mngr.session.post = types.MethodType(post, mngr.session)

            async def update_longpoll_data(self):
                self.longpoll = "updated"

            mngr.update_longpoll_data = types.MethodType(
                update_longpoll_data, mngr
            )

        self.loop.run_until_complete(prepare())

        updates = self.loop.run_until_complete(mngr.receiver())

        self.assertEqual(updates, ())
        self.assertEqual(mngr.longpoll, "updated")

        self.loop.run_until_complete(mngr.dispose())

    def test_vk_get_receiver_coroutine_function(self):
        mngr = VKManager("token")

        async def raw_request(self, method, **kwargs):
            return VKResponse(False, (), [{"id": 1, "name": "keks"}])

        mngr.raw_request = types.MethodType(raw_request, mngr)

        async def update_longpoll_data(self):
            self.longpoll = "updated"

        mngr.update_longpoll_data = types.MethodType(
            update_longpoll_data, mngr
        )

        receiver = self.loop.run_until_complete(
            mngr.get_receiver_coroutine_function()
        )

        self.assertEqual(mngr.longpoll, "updated")
        self.assertEqual(mngr.receiver, receiver)
        self.assertEqual(mngr.group_id, 1)

        self.loop.run_until_complete(mngr.dispose())

    def test_vk_msg_exec_loop(self):
        mngr = VKManager("token")

        async def raw_request(_, method, **kwargs):
            self.assertEqual(method, "execute")
            self.assertEqual(kwargs["code"], "return [API.fake.method({}),];")

            mngr.running = False

            return VKResponse(False, (), {"response": ["response"]})

        mngr.raw_request = types.MethodType(raw_request, mngr)

        request = VKRequest("fake.method", {})

        mngr.requests_queue.append(request)

        self.loop.run_until_complete(
            mngr._msg_exec_loop(None)
        )

        response = self.loop.run_until_complete(request)

        self.assertFalse(response.error)
        self.assertEqual(response.response, "response")

    def test_vk_msg_exec_loop_error(self):
        mngr = VKManager("token")

        async def raw_request(_, method, **kwargs):
            self.assertEqual(method, "execute")
            self.assertEqual(
                kwargs["code"],
                'return [API.users.get({"user_ids": "sdfsdfsdfsdfsdf"}),];'
            )

            mngr.running = False

            raw_respose = {
                "response": [False],
                "execute_errors": [
                    {
                        "method": "users.get",
                        "error_code": 113,
                        "error_msg": "Invalid user id"
                    }, {
                        "method": "execute",
                        "error_code": 113,
                        "error_msg": "Invalid user id"
                    }
                ]
            }

            return VKResponse(
                True,
                (
                    ("VK_req", raw_respose.get("error", "")),
                    ("VK_exe", raw_respose.get("execute_errors", ""))
                ),
                raw_respose.get("response", "")
            )

        mngr.raw_request = types.MethodType(raw_request, mngr)

        request = VKRequest("users.get", {"user_ids": "sdfsdfsdfsdfsdf"})

        mngr.requests_queue.append(request)

        logging.disable(logging.ERROR)

        self.loop.run_until_complete(
            mngr._msg_exec_loop(None)
        )

        logging.disable(logging.INFO)

        response = self.loop.run_until_complete(request)

        self.assertTrue(response.error)
        self.assertEqual(response.errors[0][0], "VK_req")
        self.assertEqual(response.response, "")
