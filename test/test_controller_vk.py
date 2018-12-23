from kutana import Kutana, VKManager, ExitException, Plugin
from kutana.manager.vk.environment import VKEnvironment
import unittest
import requests
import logging
import time
import json
import os


logging.disable(logging.INFO)


# These tests requires internet and token of VK user account as well as VK group.
# You can set these values through environment variables:
# TEST_TOKEN and TEST_UTOKEN.
#
# Alternatively you can use json file `configuration_test.json` with format like this:
# {
#   "token": "токен группы",
#   "utoken": "токен пользователя, который может писать в группу"
# }


class TestManagerVk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with open("configuration_test.json") as o:
                cls.conf = json.load(o)

        except FileNotFoundError:
            cls.conf = {}

        if "vk_token" not in cls.conf:
            cls.conf["vk_token"] = os.environ.get("TEST_TOKEN", "")

        if "vk_utoken" not in cls.conf:
            cls.conf["vk_utoken"] = os.environ.get("TEST_UTOKEN", "")

        cls.messages_to_delete = set()

        if not cls.conf["vk_token"] or not cls.conf["vk_utoken"]:
            raise unittest.SkipTest("No authorization found for this tests.")

        async def get_receiver_coroutine_function(self):
            actual_reci = await self.original_get_receiver_coroutine_function()

            empty_if_done = [1]

            async def reci():
                if not empty_if_done:
                    raise ExitException

                empty_if_done.pop(0)

                cls.ureq(
                    "messages.setActivity",
                    type="typing",
                    peer_id=-self.group_id
                )

                cls.messages_to_delete.add(
                    str(
                        cls.ureq(
                            "messages.send",
                            message="echo message",
                            peer_id=-self.group_id,
                            attachment= "photo-164328508_456239017," * 2
                        )
                    )
                )

                return await actual_reci()

            return reci

        VKManager.original_get_receiver_coroutine_function = VKManager.get_receiver_coroutine_function
        VKManager.get_receiver_coroutine_function = get_receiver_coroutine_function

        cls.kutana = Kutana()

        cls.kutana.add_manager(
            VKManager(
                token=cls.conf["vk_token"],
                longpoll_settings={"message_typing_state": 1}
            )
        )

    @classmethod
    def ureq(cls, method, **kwargs):
        data = {"v": "5.80"}

        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

        response = requests.post(
            "https://api.vk.com/method/{}?access_token={}".format(
                method,
                cls.conf["vk_utoken"]
            ),
            data=data
        ).json()

        time.sleep(0.34)

        return response["response"]

    @classmethod
    def tearDownClass(cls):
        VKManager.get_receiver_coroutine_function = VKManager.original_get_receiver_coroutine_function

    def tearDown(self):
        if self.messages_to_delete:
            self.ureq("messages.delete", message_ids=",".join(self.messages_to_delete), delete_for_all=1)

            self.messages_to_delete.clear()

    def test_vk_exceptions(self):
        with self.assertRaises(ValueError):
            VKManager("")

    def test_vk_wrong_token(self):
        VKManager("wrong token")

    def test_vk_no_peer_id(self):
        env = VKEnvironment(None, None)

        res = self.kutana.loop.run_until_complete(env.reply("message"))

        self.assertEqual(res, ())

    def test_vk_reply_message(self):
        messages = []

        class FakeManager:
            async def send_message(self, message, *args):
                messages.append(message)

        env = VKEnvironment(FakeManager(), peer_id=0)

        self.kutana.loop.run_until_complete(env.reply("abc"))
        self.kutana.loop.run_until_complete(env.reply("abc" * 4096))

        self.assertEqual(messages[0], "abc")
        self.assertEqual(messages[1], ("abc" * 4096)[:4096])

        self.assertEqual(len(messages), 4)

    def test_vk_manager_raw_request(self):
        async def test():
            async with VKManager("token") as mngr:
                return await mngr.raw_request("any.method", a1="v1", a2="v2")

        response = self.kutana.loop.run_until_complete(test())

        self.assertEqual(response.errors[0][1]["error_code"], 5)

    def test_vk_manager_raw_request_nested(self):
        results = []

        async def test():
            mngr = VKManager(self.conf["vk_token"])

            time.sleep(1)  # cool down vkapi

            async with mngr:
                results.append(await mngr.raw_request("users.get"))

                self.assertEqual(len(mngr.subsessions), 1)
                self.assertIsNone(mngr.subsessions[0])

                async with mngr:
                    results.append(await mngr.raw_request("users.get"))

                    self.assertEqual(len(mngr.subsessions), 2)
                    self.assertIsNone(mngr.subsessions[0])

                    session_m2 = mngr.subsessions[-1]

                    async with mngr:
                        self.assertEqual(len(mngr.subsessions), 3)
                        self.assertIsNone(mngr.subsessions[0])

                        results.append(await mngr.raw_request("users.get"))

                        session_m1 = mngr.subsessions[-1]

                    self.assertEqual(len(mngr.subsessions), 2)
                    self.assertEqual(mngr.session, session_m1)
                    self.assertIsNone(mngr.subsessions[0])

                self.assertEqual(mngr.session, session_m2)

            self.assertIsNone(mngr.session)
            self.assertFalse(mngr.subsessions)

        self.kutana.loop.run_until_complete(test())

        self.assertTrue(results)

        for r in results:
            self.assertFalse(r.error)

    def test_vk_full(self):
        plugin = Plugin()

        self.called = False
        self.called_on_raw = False
        self.called_on_attachment = False

        async def on_attachment(message, env):
            self.called_on_attachment = True
            return "GOON"

        plugin.on_attachment("photo")(on_attachment)

        async def on_regexp(message, env, match):
            attachments = message.attachments

            # Test receiving
            self.assertEqual(match.group(1), "message")
            self.assertEqual(match.group(0), "echo message")

            self.assertEqual(message.attachments, attachments)
            self.assertEqual(len(attachments), 2)

            self.assertTrue(attachments[0].link)
            self.assertTrue(attachments[1].link)

            # Test sending
            a_image = await env.upload_photo("test/test_assets/author.png")

            a_image = await env.upload_photo(
                "test/test_assets/author.png", peer_id=False
            )

            time.sleep(0.34)  # cool down vkapi

            a_audio = await env.upload_doc(
                "test/test_assets/girl.ogg",
                doctype="audio_message",
                filename="file.ogg"
            )

            self.assertTrue(a_image.id)
            self.assertTrue(a_audio.id)

            resps = await env.reply("Спасибо.", attachment=a_image)

            self.assertTrue(resps[0].response)

            for resp in resps:
                resp = await env.request(
                    "messages.delete",
                    message_ids=str(resp.response),
                    delete_for_all=1
                )

                self.assertTrue(resp.response)

            # Test failed request
            resp = await env.request("messages.send")

            self.assertTrue(resp.error)
            self.assertTrue(resp.errors[0][1])
            self.assertEqual(resp.errors[0][0], "VK_req")
            self.assertFalse(resp.response)

            self.called = True

        plugin.on_regexp_text(r"echo (.+)")(on_regexp)

        async def on_raw(update, env):
            self.called_on_raw = True

            return "GOON"

        plugin.on_raw()(on_raw)

        self.kutana.executor.register_plugins([plugin])

        self.kutana.run()

        self.assertTrue(self.called)
        self.assertTrue(self.called_on_raw)
        self.assertTrue(self.called_on_attachment)
