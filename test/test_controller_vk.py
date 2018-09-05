from kutana import Kutana, VKController, ExitException, Plugin, \
    logger
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


class TestControllerVk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with open("configuration_test.json") as o:
                cls.conf = json.load(o)

        except FileNotFoundError:
            cls.conf = {
                "vk_token": os.environ.get("TEST_TOKEN", ""),
                "vk_utoken": os.environ.get("TEST_UTOKEN", ""),
            }

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

        VKController.original_get_receiver_coroutine_function = VKController.get_receiver_coroutine_function
        VKController.get_receiver_coroutine_function = get_receiver_coroutine_function

        cls.kutana = Kutana()

        cls.kutana.add_controller(
            VKController(
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
        VKController.get_receiver_coroutine_function = VKController.original_get_receiver_coroutine_function

    def tearDown(self):
        if self.messages_to_delete:
            self.ureq("messages.delete", message_ids=",".join(self.messages_to_delete), delete_for_all=1)

            self.messages_to_delete.clear()

    def test_exceptions(self):
        with self.assertRaises(ValueError):
            VKController("")

        with self.assertRaises(RuntimeError):
            self.kutana.loop.run_until_complete(
                VKController("token").raw_request("any.method")
            )

    def test_vk_full(self):
        plugin = Plugin()

        self.called = False
        self.called_on_attachment = False

        async def on_attachment(*args, **kwargs):
            self.called_on_attachment = True
            return "GOON"

        plugin.on_attachment("photo")(on_attachment)

        async def on_regexp(message, attachments, env, **kwargs):
            # Test receiving
            self.assertEqual(env.match.group(1), "message")
            self.assertEqual(env.match.group(0), "echo message")

            self.assertEqual(message.attachments, attachments)
            self.assertEqual(len(attachments), 2)

            self.assertTrue(attachments[0].link)
            self.assertTrue(attachments[1].link)

            # Test sending
            a_image = await env.upload_photo("test/test_assets/author.png")
            a_image = await env.upload_photo("test/test_assets/author.png", peer_id=False)
            a_audio = await env.upload_doc("test/test_assets/girl.ogg", doctype="audio_message", filename="file.ogg")

            self.assertTrue(a_image.id)
            self.assertTrue(a_audio.id)

            resp = await env.reply("Спасибо.", attachment=a_image)

            self.assertTrue(resp.response)

            resp = await env.request("messages.delete", message_ids=str(resp.response), delete_for_all=1)

            self.assertTrue(resp.response)

            # Test failed request
            resp = await env.request("wrong.method")

            self.assertTrue(resp.error)
            self.assertFalse(resp.response)

            self.called = True

        plugin.on_regexp_text(r"echo (.+)")(on_regexp)

        async def on_raw(*args, **kwargs):
            return "GOON"

        plugin.on_raw()(on_raw)

        self.kutana.executor.register_plugins(plugin)

        self.kutana.run()

        self.assertTrue(self.called)
        self.assertTrue(self.called_on_attachment)
