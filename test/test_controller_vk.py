from kutana import Kutana, VKController, ExitException, Plugin, \
    logger, create_vk_env
import unittest
import requests
import time
import json
import os


logger.setLevel(40)  # ERROR LEVEL


# Theese tests requires internet and token of VK user account as well as VK group.
# You can set these values through environment variables:
# TEST_TOKEN and TEST_UTOKEN.
#
# Alternatively you can use json file `configuration_test.json` with format like this:
# {
#   "token": "токен группы",
#   "utoken": "токен пользователя. который модет писать в группу"
# }


class TestControllerVk(unittest.TestCase):
    def setUp(self):
        try:
            with open("configuration_test.json") as o:
                self.conf = json.load(o)

        except FileNotFoundError:
            self.conf = {
                "token": os.environ.get("TEST_TOKEN", ""),
                "utoken": os.environ.get("TEST_UTOKEN", ""),
            }

        self.messages_to_delete = set()
        this_case = self

        if not self.conf["token"] or not self.conf["utoken"]:
            self.skipTest("No authorization found for tests.")

        async def create_receiver(self):
            actual_reci = await self.original_create_receiver()

            empty_if_done = [1]

            async def reci():
                if not empty_if_done:
                    raise ExitException

                empty_if_done.pop(0)

                this_case.messages_to_delete.add(
                    str(
                        this_case.ureq(
                            "messages.send",
                            message="echo message",
                            peer_id=-self.group_id
                        )
                    )
                )

                return await actual_reci()

            return reci

        VKController.original_create_receiver = VKController.create_receiver
        VKController.create_receiver = create_receiver

        self.kutana = Kutana()

        self.kutana.apply_environment(
            create_vk_env(token=self.conf["token"])
        )

    def ureq(self, method, **kwargs):
        data = {"v": "5.80"}

        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

        response = requests.post(
            "https://api.vk.com/method/{}?access_token={}".format(
                method,
                self.conf["utoken"]
            ),
            data=data
        ).json()

        time.sleep(0.34)

        return response["response"]

    def tearDown(self):
        VKController.create_receiver = VKController.original_create_receiver

        self.ureq("messages.delete", message_ids=",".join(self.messages_to_delete), delete_for_all=1)

    def test_controller_vk(self):
        plugin = Plugin()

        self.called = False

        async def on_regexp(message, env, **kwargs):
            self.assertEqual(env.match.group(1), "message")
            self.assertEqual(env.match.group(0), "echo message")

            a_image = await env.upload_photo("test/author.png")
            a_audio = await env.upload_doc("test/girl.ogg", doctype="audio_message", filename="file.ogg")

            self.assertTrue(a_image.id)
            self.assertTrue(a_audio.id)

            resp = await env.reply("Спасибо.", attachment=a_image)

            self.assertTrue(resp.response)

            resp = await env.request("messages.delete", message_ids=str(resp.response), delete_for_all=1)

            self.assertTrue(resp.response)

            self.called = True

        plugin.on_regexp_text(r"echo (.+)")(on_regexp)

        self.kutana.executor.register_plugins(plugin)

        self.kutana.run()

        self.assertTrue(self.called)
