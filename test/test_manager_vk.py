import asyncio
import json
import logging
import types
import unittest

import aiohttp
from kutana import (Attachment, VKEnvironment, VKManager, VKRequest,
                    VKResponse, set_logger_level)


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

        class FakeSession:
            def post(self, url, data):
                class FakePost:
                    def __init__(self, url, data):
                        pass

                    async def __aenter__(self):
                        class FakeResponse:
                            status = 200

                            async def text(self):
                                return json.dumps(
                                    {"error":{"error_code":5,"error_msg":"User authori"
                                    "zation failed: invalid access_token (4).",
                                    "request_params":[{"key":"oauth","value":"1"},
                                    {"key":"method","value":"any.method"},{"key":"v",
                                    "value":"5.80"},{"key":"a1","value":"v1"},{
                                    "key":"a2","value":"v2"}]}}
                                )

                        return FakeResponse()

                    async def __aexit__(self, exc_type, exc, tb):
                        pass

                return FakePost(url, data)

            async def close(self):
                pass

        async def test():
            mngr.session = FakeSession()

            set_logger_level(logging.CRITICAL)

            response = await mngr.raw_request("any.method", a1="v1", a2="v2")

            set_logger_level(logging.ERROR)

            self.assertEqual(response.errors[0][1]["error_code"], 5)

        self.loop.run_until_complete(
            test()
        )

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
            mngr.send_message(
                "text for message", 0, ["attachment"], random_id=0, _timeout=0
            )
        )

        response = responses[0]

        self.assertTrue(response.error)
        self.assertEqual(len(mngr.requests_queue), 1)
        self.assertEqual(mngr.requests_queue[0].method, "messages.send")
        self.assertEqual(mngr.requests_queue[0].kwargs, {
            "message": "text for message",
            "attachment": "attachment,",
            "peer_id": 0, "random_id": 0
        })

    def test_vk_manager_send_message_long(self):
        mngr = VKManager("token")

        responses = self.loop.run_until_complete(
            mngr.send_message(
                "a" * 6000, 0, random_id=0, _timeout=0
            )
        )

        self.assertEqual(len(responses), 2)

        self.assertTrue(responses[0].error)
        self.assertTrue(responses[1].error)

        self.assertEqual(len(mngr.requests_queue), 2)

        self.assertEqual(mngr.requests_queue[0].method, "messages.send")
        self.assertEqual(mngr.requests_queue[0].kwargs["message"], "a" * 4096)
        self.assertTrue(mngr.requests_queue[0].kwargs["random_id"])

        self.assertEqual(mngr.requests_queue[1].method, "messages.send")
        self.assertEqual(mngr.requests_queue[1].kwargs["message"],
                         "a" * (6000 - 4096))
        self.assertEqual(mngr.requests_queue[1].kwargs["random_id"], 0)

    def test_vk_manager_send_message_attachment(self):
        mngr = VKManager("token")

        attachment = Attachment("photo", 1, 0, None, None, None)

        responses = self.loop.run_until_complete(
            mngr.send_message(
                "text for message", 0, attachment, _timeout=0
            )
        )

        response = responses[0]

        self.assertTrue(response.error)
        self.assertEqual(len(mngr.requests_queue), 1)
        self.assertEqual(mngr.requests_queue[0].method, "messages.send")
        self.assertIsNotNone(mngr.requests_queue[0].kwargs.get("random_id"))
        self.assertEqual(mngr.requests_queue[0].kwargs, {
            "message": "text for message",
            "attachment": "photo0_1,",
            "peer_id": 0,
            "random_id": mngr.requests_queue[0].kwargs.get("random_id")
        })

    def test_vk_manager_create_attachment(self):
        test_attachment_raw = {
            "id": 13, "album_id": 13, "owner_id": 1, "sizes":
            [{"type": "s", "url": "url", "width": 0, "height": 0}],
            "text": "", "date": 0, "post_id": 0, "likes":
            {"user_likes": 0, "count": 577904}, "comments": {"count": 421},
            "can_comment": 1, "can_repost": 1, "tags": {"count": 0}
        }

        attachment = VKManager.create_attachment(
            test_attachment_raw, "photo"
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "photo")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_create_attachment_no_type(self):
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

        attachment = VKManager.create_attachment(
            test_attachment_raw
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "photo")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_create_attachment_doc(self):
        test_attachment_raw = {
            "id": 13, "owner_id": 1, "title": "rrrrr.png", "size": 119900,
            "ext": "png", "url": "url", "date": 0, "type": 4,
        }

        attachment = VKManager.create_attachment(
            test_attachment_raw, "doc"
        )

        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.type, "doc")
        self.assertEqual(attachment.owner_id, 1)
        self.assertEqual(attachment.access_key, None)
        self.assertEqual(attachment.link, "url")
        self.assertEqual(attachment.raw_attachment, test_attachment_raw)

    def test_vk_manager_create_attachment_doc_no_link(self):
        test_attachment_raw = {
            "id": 13, "owner_id": 1, "title": "rrrrr.png", "size": 119900,
            "ext": "png", "date": 0, "type": 4,
        }

        attachment = VKManager.create_attachment(
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

            class FakeSession:
                def post(self, url):
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

                    return FakePost(url)

                async def close(self):
                    pass

            mngr.session = FakeSession()

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

            class FakeSession:
                def post(self, url):
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

                    return FakePost(url)

                async def close(self):
                    pass

            mngr.session = FakeSession()

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

    def test_vk_exec_loop(self):
        mngr = VKManager("token")

        async def raw_request(_, method, **kwargs):
            self.assertEqual(method, "execute")
            self.assertEqual(kwargs["code"], "return [API.fake.method({}),];")

            mngr.running = False

            return VKResponse(False, (), {"response": ["response"]})

        mngr.raw_request = types.MethodType(raw_request, mngr)

        req = VKRequest("fake.method", {})

        mngr.requests_queue.append(req)

        tasks = []
        def ensure(task):
            _task = asyncio.ensure_future(task, loop=self.loop)
            tasks.append(_task)
            return _task

        self.loop.run_until_complete(
            mngr._exec_loop(ensure)
        )

        self.loop.run_until_complete(asyncio.gather(*tasks))

        response = self.loop.run_until_complete(req)

        self.assertFalse(response.error)
        self.assertEqual(response.response, "response")

    def test_vk_exec_loop_error(self):
        mngr = VKManager("token")

        async def raw_request(_, method, **kwargs):
            self.assertEqual(method, "execute")
            self.assertEqual(
                kwargs["code"],
                'return [API.users.get({"user_ids": "sdfsdfsdfsdfsdf"}),];'
            )

            mngr.running = False

            raw_response = {
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
                    ("VK_req", raw_response.get("error", "")),
                    ("VK_exe", raw_response.get("execute_errors", ""))
                ),
                raw_response.get("response", "")
            )

        mngr.raw_request = types.MethodType(raw_request, mngr)

        req = VKRequest("users.get", {"user_ids": "sdfsdfsdfsdfsdf"})

        mngr.requests_queue.append(req)

        logging.disable(logging.ERROR)

        tasks = []
        def ensure(task):
            _task = asyncio.ensure_future(task, loop=self.loop)
            tasks.append(_task)
            return _task

        self.loop.run_until_complete(
            mngr._exec_loop(ensure)
        )

        self.loop.run_until_complete(asyncio.gather(*tasks))

        logging.disable(logging.INFO)

        response = self.loop.run_until_complete(req)

        self.assertTrue(response.error)
        self.assertEqual(response.errors[0][0], "VK_req")
        self.assertEqual(response.response, "")

    @staticmethod
    def get_fake_manager(actions):
        class FakeManager:
            group_id = 10

            @staticmethod
            def create_attachment(att, typ):
                actions.append((att, typ))

                return "file"

            async def request(self, method, **kwargs):
                if method == "docs.getMessagesUploadServer":
                    actions.append((method, kwargs))
                    return VKResponse(False, (), {"upload_url": "url1"})

                if method == "docs.getWallUploadServer":
                    actions.append((method, kwargs))
                    return VKResponse(False, (), {"upload_url": "url2"})

                if method == "photos.getMessagesUploadServer":
                    actions.append((method, kwargs))
                    return VKResponse(False, (), {"upload_url": "url3"})

                if method == "photos.saveMessagesPhoto":
                    actions.append((method, kwargs))
                    return VKResponse(False, (), ["attachment"])

                if method == "docs.save":
                    actions.append((method, kwargs))
                    return VKResponse(False, (), "attachment")

                raise ValueError

        return FakeManager()

    def test_vk_upload_doc(self):
        actions = []

        env = VKEnvironment(self.get_fake_manager(actions), None)

        async def _upload_file_to_vk(self, url, data):
            return {"doc": "upload"}

        env.replace_method("_upload_file_to_vk", _upload_file_to_vk)

        attachment = self.loop.run_until_complete(
            env.upload_doc(b"file")
        )

        self.assertEqual(attachment, "file")

        self.assertEqual(len(actions), 3)

        self.assertEqual(
            actions[0], ('docs.getWallUploadServer', {'group_id': 10})
        )

        self.assertEqual(
            actions[1], ('docs.save', {'doc': 'upload'})
        )

        self.assertEqual(
            actions[2], ('attachment', 'doc')
        )

    def test_vk_upload_doc_w_peer_id(self):
        actions = []

        env = VKEnvironment(self.get_fake_manager(actions), None)

        async def _upload_file_to_vk(self, url, data):
            return {"doc": "upload"}

        env.replace_method("_upload_file_to_vk", _upload_file_to_vk)

        attachment = self.loop.run_until_complete(
            env.upload_doc(b"file", peer_id=2)
        )

        self.assertEqual(attachment, "file")

        self.assertEqual(len(actions), 3)

        self.assertEqual(
            actions[0],
            ('docs.getMessagesUploadServer', {'peer_id': 2, 'type': 'doc'})
        )

        self.assertEqual(
            actions[1], ('docs.save', {'doc': 'upload'})
        )

        self.assertEqual(
            actions[2], ('attachment', 'doc')
        )

    def test_vk_upload_photo(self):
        actions = []

        env = VKEnvironment(self.get_fake_manager(actions), None)

        async def _upload_file_to_vk(self, url, data):
            return {"doc": "upload"}

        env.replace_method("_upload_file_to_vk", _upload_file_to_vk)

        attachment = self.loop.run_until_complete(
            env.upload_photo(b"file")
        )

        self.assertEqual(attachment, "file")

        self.assertEqual(len(actions), 3)

        self.assertEqual(
            actions[0], ('photos.getMessagesUploadServer', {'peer_id': None})
        )

        self.assertEqual(
            actions[1], ('photos.saveMessagesPhoto', {'doc': 'upload'})
        )

        self.assertEqual(
            actions[2], ('attachment', 'photo')
        )

    def test_vk_upload_photo_w_peer_id(self):
        actions = []

        env = VKEnvironment(self.get_fake_manager(actions), None)

        async def _upload_file_to_vk(self, url, data):
            return {"doc": "upload"}

        env.replace_method("_upload_file_to_vk", _upload_file_to_vk)

        attachment = self.loop.run_until_complete(
            env.upload_photo(b"file", peer_id=2)
        )

        self.assertEqual(attachment, "file")

        self.assertEqual(len(actions), 3)

        self.assertEqual(
            actions[0],
            ('photos.getMessagesUploadServer', {'peer_id': 2})
        )

        self.assertEqual(
            actions[1], ('photos.saveMessagesPhoto', {'doc': 'upload'})
        )

        self.assertEqual(
            actions[2], ('attachment', 'photo')
        )

    def test_upload_file_to_vk(self):
        class FakePost:
            def __init__(self, url, data):
                pass

            async def __aenter__(self):
                class FakeResponse:
                    status = 200

                    async def text(self):
                        return json.dumps({"test": "test"})

                return FakeResponse()

            async def __aexit__(self, exc_type, exc, tb):
                pass

        class Session:
            post = FakePost

        class Manager:
            session = Session()

        env = VKEnvironment(Manager(), None)

        result = self.loop.run_until_complete(
            env._upload_file_to_vk("nice_url", {"nice": "data"})
        )

        self.assertEqual(result, {"test": "test"})

    def test_upload_file_to_vk_error(self):
        class FakePost:
            def __init__(self, url, data):
                pass

            async def __aenter__(self):
                class FakeResponse:
                    status = 200

                    async def text(self):
                        return json.dumps({"error": "exists"})

                return FakeResponse()

            async def __aexit__(self, exc_type, exc, tb):
                pass

        class Session:
            post = FakePost

        class Manager:
            session = Session()

        env = VKEnvironment(Manager())

        result = self.loop.run_until_complete(
            env._upload_file_to_vk("nice_url", {"nice": "data"})
        )

        self.assertEqual(result, None)

    def test_vk_get_file_from_attachment_empty(self):
        mngr = VKManager("token")

        async def test():
            mngr.session = aiohttp.ClientSession()

            env = VKEnvironment(mngr)

            res = await env.get_file_from_attachment(None)

            self.assertEqual(res, None)

            res = await env.get_file_from_attachment(
                Attachment("photo", 13, 1, None, None, {})
            )

            self.assertEqual(res, None)

        self.loop.run_until_complete(test())

        self.loop.run_until_complete(mngr.dispose())
