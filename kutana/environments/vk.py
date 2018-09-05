from kutana.executor import Executor
from kutana.plugins.data import Attachment
from kutana.environments.vk_helpers import upload_doc_class, upload_photo_class
from kutana.controllers.vk import VKController
import json


def create_vk_env(token=None, configuration=None):
    """Create controller and executor for working with vk.com"""

    if isinstance(configuration, str):
        with open(configuration) as o:
            configuration = json.load(o)

    elif hasattr(configuration, 'read'):
        configuration = json.load(o)

    if isinstance(configuration, dict):
        if token is None:
            token = configuration["token"]

    if not token:
        raise ValueError("No token.")

    controller = VKController(token)

    executor = Executor()

    async def generic_answer(message, peer_id, attachment=None, sticker_id=None, payload=None, keyboard=None):
        if isinstance(attachment, Attachment):
            attachment = [attachment]

        if isinstance(attachment, (list, tuple)):
            new_attachment = ""

            for a in attachment:
                if isinstance(a, Attachment):
                    new_attachment += \
                        "{}{}_{}".format(a.type, a.owner_id, a.id) + \
                        ("_" + a.access_key if a.access_key else "")

                else:
                    new_attachment += str(a)

                new_attachment += ","

            attachment = new_attachment

        return await controller.request(
            "messages.send",
            message=message,
            peer_id=peer_id,
            attachment=attachment,
            sticker_id=sticker_id,
            payload=sticker_id,
            keyboard=keyboard
        )

    async def build_vk_environment(controller_type, update, env):
        if controller_type != "vk":
            return

        if update["type"] == "message_new":
            async def concrete_answer(message, attachment=None, sticker_id=None, payload=None, keyboard=None):
                return await generic_answer(
                    message,
                    update["object"]["peer_id"],
                    attachment,
                    sticker_id,
                    payload,
                    keyboard
                )

            env["reply"] = concrete_answer

        env["send_msg"] = generic_answer

        env["upload_photo"] = upload_photo_class(controller, update["object"].get("peer_id"))
        env["upload_doc"] = upload_doc_class(controller, update["object"].get("peer_id"))

        env["request"] = controller.request

    executor.register(build_vk_environment)

    async def prc_err(controller_type, update, env):
        if update["type"] == "message_new":
            await env.reply("Произошла ошибка! Приносим свои извинения.")

    executor.register(prc_err, error=True)

    return {
        "controller": controller,
        "executor": executor,
    }
