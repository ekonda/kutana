import asyncio
import json
import logging
import types
import unittest

import aiohttp
from kutana import (Attachment, ExitException, Kutana, Plugin, TGManager,
                    TGResponse)
from kutana.manager.tg.environment import TGAttachmentTemp


class TestManagerVk(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        logging.disable(logging.INFO)

    def tearDown(self):
        logging.disable(logging.DEBUG)

    def test_tg_exceptions(self):
        with self.assertRaises(ValueError):
            TGManager("")

    def test_tg_get_background_coroutines(self):
        mngr = TGManager("token")

        self.assertEqual(
            self.loop.run_until_complete(
                mngr.get_background_coroutines(None)
            ),
            ()
        )

    def test_tg_environmnet(self):
        mngr = TGManager("token")

        env = self.loop.run_until_complete(
            mngr.get_environment({"message": {"chat": {"id": 1}}})
        )

        self.assertEqual(env.peer_id, 1)

        env = self.loop.run_until_complete(
            mngr.get_environment({})
        )

        self.assertEqual(env.peer_id, None)

    def test_tg_upload_methods(self):
        mngr = TGManager("token")

        env = self.loop.run_until_complete(
            mngr.get_environment({"message": {"chat": {"id": 1}}})
        )

        photo_a = self.loop.run_until_complete(
            env.upload_photo("photo")
        )

        self.assertEqual(photo_a.type, "photo")
        self.assertEqual(photo_a.content, "photo")
        self.assertEqual(photo_a.kwargs, {})

        document_a = self.loop.run_until_complete(
            env.upload_doc("document")
        )

        self.assertEqual(document_a.type, "doc")
        self.assertEqual(document_a.content, "document")
        self.assertEqual(document_a.kwargs, {})

    def test_tg_replay(self):
        mngr = TGManager("token")

        env = self.loop.run_until_complete(
            mngr.get_environment({"message": {"chat": {"id": 1}}})
        )

        async def request(_, method, **kwargs):
            self.assertEqual(kwargs["chat_id"], "1")

            return TGResponse(True, (), "")

        mngr.request = types.MethodType(request, mngr)

        res = self.loop.run_until_complete(
            env.reply("hi")
        )

        self.assertTrue(res[0].error)
        self.assertFalse(res[0].response)

    def test_tg_get_file_from_attachment(self):
        mngr = TGManager("token")

        env = self.loop.run_until_complete(
            mngr.get_environment({"message": {"chat": {"id": 1}}})
        )

        async def request(_, method, **kwargs):
            self.assertEqual(kwargs["file_id"], 13)

            return TGResponse(False, (), {"file_path": "path"})

        mngr.request = types.MethodType(request, mngr)

        async def request_file(_, path):
            self.assertEqual(path, "path")

            return "file"

        mngr.request_file = types.MethodType(request_file, mngr)

        attachment = Attachment("photo", 13, None, None, None, None)

        file = self.loop.run_until_complete(
            env.get_file_from_attachment(attachment)
        )

        self.assertEqual(file, "file")

    def test_tg_get_file_from_attachment_error(self):
        mngr = TGManager("token")

        env = self.loop.run_until_complete(
            mngr.get_environment({"message": {"chat": {"id": 1}}})
        )

        async def request(_, method, **kwargs):
            self.assertEqual(kwargs["file_id"], 13)

            return TGResponse(True, (), "")

        mngr.request = types.MethodType(request, mngr)

        attachment = Attachment("photo", 13, None, None, None, None)

        file = self.loop.run_until_complete(
            env.get_file_from_attachment(attachment)
        )

        self.assertEqual(file, None)

    def test_tg_request_file_none(self):
        mngr = TGManager("token")

        mngr.file_url = "wrong_url"

        res = self.loop.run_until_complete(
            mngr.request_file("path")
        )

        self.assertEqual(res, None)

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_tg_send_message(self):
        mngr = TGManager("token")

        attachment1 = Attachment("photo", 13, None, None, None, None)
        attachment2 = TGAttachmentTemp("bad_type", "strange_content", {})

        async def request(self, method, **kwargs):
            return TGResponse(
                False, (), [method, kwargs]
            )

        mngr.request = types.MethodType(request, mngr)

        res0 = self.loop.run_until_complete(
            mngr.send_message("hi", None)
        )

        self.assertEqual(len(res0), 0)

        res1 = self.loop.run_until_complete(
            mngr.send_message("hi", 1, [attachment1, attachment2])
        )

        self.assertEqual(len(res1), 2)

        self.assertEqual(
            res1[0].response, ["sendMessage", {"chat_id": '1', "text": "hi"}]
        )

        self.assertEqual(
            res1[1].response, ["sendPhoto", {"chat_id": '1', "photo": "13"}]
        )

        res2 = self.loop.run_until_complete(
            mngr.send_message("", 1, attachment1)
        )

        self.assertEqual(len(res2), 1)

        self.assertEqual(
            res2[0].response, ["sendPhoto", {"chat_id": '1', "photo": "13"}]
        )

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_tg_create_attachment(self):
        attachment = TGManager.create_attachment(
            {"file_id": 13}, "document"
        )

        self.assertEqual(attachment.type, "doc")
        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.link, None)

        attachment = TGManager.create_attachment(
            [{"file_id": 13}], "photo"
        )

        self.assertEqual(attachment.type, "photo")
        self.assertEqual(attachment.id, 13)
        self.assertEqual(attachment.link, None)

        attachment = TGManager.create_attachment(None, "video")

        self.assertEqual(attachment, None)


    def test_tg_create_message(self):
        mngr = TGManager("token")

        message = self.loop.run_until_complete(
            mngr.create_message({"message": {
                "text": "text",
                "from": {"id": 1},
                "chat": {"id": 2},
                "date": 0
            }})
        )

        self.assertEqual(message.text, "text")
        self.assertEqual(message.attachments, ())
        self.assertEqual(message.from_id, 1)
        self.assertEqual(message.peer_id, 2)
        self.assertEqual(message.date, 0)

        message = self.loop.run_until_complete(
            mngr.create_message({})
        )

        self.assertEqual(message, None)

    def test_vk_request(self):
        mngr = TGManager("token")

        async def prepare():
            class FakeSession:
                def post(self, url, proxy, data):
                    class FakePost:
                        def __init__(self, url, proxy, data):
                            pass

                        async def __aenter__(self):
                            class FakeResponse:
                                async def text(self):
                                    return json.dumps({
                                        "ok": True,
                                        "result": "result"
                                    })

                            return FakeResponse()

                        async def __aexit__(self, exc_type, exc, tb):
                            pass

                    return FakePost(url, proxy, data)

                async def close(self):
                    pass

            mngr.session = FakeSession()

        self.loop.run_until_complete(prepare())

        response = self.loop.run_until_complete(
            mngr.request("method", a1="v1", a2="v2")
        )

        self.assertEqual(response.error, False)
        self.assertEqual(response.response, "result")
        self.assertEqual(response.errors, ())

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_vk_request_error(self):
        mngr = TGManager("token")

        exception = None

        async def prepare():
            class FakeSession:
                def post(self, url, proxy, data):
                    class FakePost:
                        def __init__(self, url, proxy, data):
                            pass

                        async def __aenter__(self):
                            class FakeResponse:
                                async def text(self):
                                    if exception:
                                        raise exception

                                    return json.dumps({
                                        "ok": False
                                    })

                            return FakeResponse()

                        async def __aexit__(self, exc_type, exc, tb):
                            pass

                    return FakePost(url, proxy, data)

                async def close(self):
                    pass

            mngr.session = FakeSession()

        self.loop.run_until_complete(prepare())

        response = self.loop.run_until_complete(
            mngr.request("method1", a1="v1", a2="v2")
        )

        self.assertEqual(response.error, True)
        self.assertEqual(response.response, "")
        self.assertTrue(response.errors)

        exception = aiohttp.ClientError

        response = self.loop.run_until_complete(
            mngr.request("method2", a1="v1", a2="v2")
        )

        self.assertEqual(response.error, True)
        self.assertEqual(response.response, "")
        self.assertTrue(response.errors)

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_tg_receiver(self):
        mngr = TGManager("token")

        async def request(self, method, **kwargs):
            if method == "getUpdates":
                return TGResponse(
                    False, (), [{"update_id": 10}]
                )

        mngr.request = types.MethodType(request, mngr)

        updates = self.loop.run_until_complete(
            mngr.receiver()
        )

        self.assertEqual(updates, [{"update_id": 10}])

        self.loop.run_until_complete(
            mngr.dispose()
        )

    def test_tg_receiver_error(self):
        mngr = TGManager("token")

        async def request(self, method, **kwargs):
            if method == "getUpdates":
                return TGResponse(True, (), "")

        mngr.request = types.MethodType(request, mngr)

        updates = self.loop.run_until_complete(
            mngr.receiver()
        )

        self.assertEqual(updates, ())

        self.loop.run_until_complete(mngr.dispose())

    def test_tg_get_receiver_coroutine_function(self):
        mngr = TGManager("token")

        async def request(self, method, **kwargs):
            if method == "getMe":
                return TGResponse(
                    False,
                    (),
                    {"first_name": "A", "last_name": "B", "username": "a"}
                )

        mngr.request = types.MethodType(request, mngr)

        receiver = self.loop.run_until_complete(
            mngr.get_receiver_coroutine_function()
        )

        self.assertEqual(receiver, mngr.receiver)

        self.loop.run_until_complete(mngr.dispose())

    def test_tg_get_receiver_coroutine_function_error(self):
        mngr = TGManager("token")

        async def request(self, method, **kwargs):
            if method == "getMe":
                return TGResponse(True, (), {})

        mngr.request = types.MethodType(request, mngr)

        with self.assertRaises(ValueError):
            self.loop.run_until_complete(
                mngr.get_receiver_coroutine_function()
            )

        self.loop.run_until_complete(mngr.dispose())
