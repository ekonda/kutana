from kutana.controllers.vk.methodclasses import (
    upload_doc_class, upload_photo_class, reply_concrete_class
)
from kutana.controllers.vk.converter import convert_to_message
from kutana.controllers.vk.vkcontrollerdata import VKRequest, VKResponse
from kutana.controllers.basic import BasicController
from kutana.plugindata import Attachment
from kutana.logger import logger
import asyncio
import aiohttp
import json


class VKController(BasicController):
    """Class for receiving updates from vk.com.
    Controller requires group's token. You can specify settings for
    groups.setLongPollSettings with argument `longpoll_settings`.
    """

    type = "vk"

    def __init__(self, token, longpoll_settings=None):
        if not token:
            raise ValueError("No `token` specified")

        if not longpoll_settings:
            longpoll_settings = {}

        self.session = None
        self.group_id = None
        self.longpoll = None

        self.running = True
        self.requests_queue = []

        self.version = "5.80"
        self.token = token
        self.longpoll_settings = longpoll_settings

        self.api_url = "https://api.vk.com/method/{{}}?access_token={}&v={}" \
            .format(self.token, self.version)
        self.longpoll_url = "{}?act=a_check&key={}&wait=25&ts={}"

    async def raw_request(self, method, **kwargs):
        """Perform api request to vk.com"""

        if not self.session:
            raise RuntimeError("Session is not created yet")

        url = self.api_url.format(method)

        data = {}

        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

        try:
            async with self.session.post(url, data=data) as response:
                raw_respose = await response.json()

        except Exception as e:
            return VKResponse(
                error=True,
                kutana_error=(type(e), str(e)),
                response_error=("", ""),
                response="",
                execute_errors=""
            )

        if raw_respose is None or not isinstance(raw_respose, dict):
            return VKResponse(
                error=True,
                kutana_error=("", ""),
                response_error=("Unknown response", raw_respose),
                response="",
                execute_errors=raw_respose.get("execute_errors", "")
            )

        if not raw_respose.get("response") or raw_respose.get("error"):
            return VKResponse(
                error=True,
                kutana_error=("", ""),
                response_error=("Error", raw_respose["error"]),
                response=raw_respose.get("response", ""),
                execute_errors=raw_respose.get("execute_errors", "")
            )

        return VKResponse(
            error=False,
            kutana_error=("", ""),
            response_error=("", ""),
            response=raw_respose["response"],
            execute_errors=raw_respose.get("execute_errors", "")
        )

    async def request(self, method, **kwargs):
        """Shedule execution of request to vk.com and return result."""

        request = VKRequest(
            method,
            **kwargs
        )

        self.requests_queue.append(request)

        await request

        try:
            return await asyncio.wait_for(request, timeout=10)

        except asyncio.TimeoutError:
            return VKResponse(
                error=True,
                kutana_error=(
                    "Timeout",
                    "Request took too long and was forgotten."
                ),
                response_error=("", ""),
                response="",
                execute_errors=""
            )

    async def send_message(self, message, peer_id, attachment=None,
            sticker_id=None, payload=None, keyboard=None):
        """Send message to target peer_id wiith parameters."""

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

        return await self.request(
            "messages.send",
            message=message,
            peer_id=peer_id,
            attachment=attachment,
            sticker_id=sticker_id,
            payload=sticker_id,
            keyboard=keyboard
        )\

    async def setup_env(self, update, eenv):
        peer_id = update["object"].get("peer_id")

        if update["type"] == "message_new":
            eenv["reply"] = reply_concrete_class(self, peer_id)

        eenv["send_message"] = self.send_message

        eenv["upload_photo"] = upload_photo_class(self, peer_id)
        eenv["upload_doc"] = upload_doc_class(self, peer_id)

        eenv["request"] = self.request

    async def convert_to_message(self, update, eenv):
        return await convert_to_message(update, eenv)

    @staticmethod
    async def _set_results_to_requests(result, requests):
        err_no = 0

        for res, req in zip(result.response, requests):
            if res is False:
                if len(result.execute_errors) > err_no:
                    known_error = result.execute_errors[err_no]
                    err_no += 1

                else:
                    known_error = ""

                res = VKResponse(
                    error=True,
                    kutana_error=("", ""),
                    response_error=(
                        "Error" if known_error else "Unknown error",
                        known_error
                    ),
                    response="",
                    execute_errors=result.execute_errors
                )

            else:
                res = VKResponse(
                    error=False,
                    kutana_error=("", ""),
                    response_error=("", ""),
                    response=res,
                    execute_errors=""
                )

            try:
                req.set_result(res)
            except asyncio.InvalidStateError:
                pass

    async def _msg_exec_loop(self, ensure_future):
        while self.running:
            requests = []

            await asyncio.sleep(0)

            for _ in range(25):
                if not self.requests_queue:
                    break

                requests.append(self.requests_queue.pop(0))

            if not requests:
                continue

            code = "return ["

            for r in requests:
                code += "API.{}({}),".format(
                    r.method, json.dumps(r.kwargs, ensure_ascii=False)
                )

            code += "];"

            result = await self.raw_request("execute", code=code)

            if result.error:
                logger.error(result.kutana_error + result.response_error)

            await ensure_future(self._set_results_to_requests(result, requests))

    async def get_background_coroutines(self, ensure_future):
        return (self._msg_exec_loop(ensure_future),)

    async def update_longpoll_data(self):
        longpoll = await self.raw_request("groups.getLongPollServer", group_id=self.group_id)

        if longpoll.error:
            raise ValueError(
                "Couldn't get longpoll information\n{}"
                .format(
                    longpoll.kutana_error +
                    longpoll.response_error
                )
            )

        self.longpoll = {
            **longpoll.response
        }

    async def receiver(self):
        async with self.session.post(self.longpoll_url.format(
            self.longpoll["server"],
            self.longpoll["key"],
            self.longpoll["ts"],
        )) as resp:
            try:
                response = await resp.json()
            except Exception:
                return []

        if "ts" in response:
            self.longpoll["ts"] = response["ts"]

        if "failed" in response:
            if response["failed"] in (2, 3, 4):
                await self.update_longpoll_data()

            return

        updates = []

        for update in response["updates"]:
            if "type" not in update or "object" not in update:
                continue

            updates.append(update)

        return updates

    async def get_receiver_coroutine_function(self):
        self.session = aiohttp.ClientSession()

        current_group_s = await self.raw_request("groups.getById")

        if current_group_s.error or not current_group_s.response[0].get("id"):
            raise ValueError(
                "Couldn't get group information\n{}"
                .format(
                    current_group_s.kutana_error +
                    current_group_s.response_error
                )
            )

        self.group_id = current_group_s.response[0]["id"]

        await self.raw_request(
            "groups.setLongPollSettings",
            group_id=self.group_id,
            api_version=self.version,
            enabled=1,
            **{
                **dict(
                    message_reply=0,
                    message_allow=0,
                    message_deny=0,
                    message_edit=0,
                    photo_new=0,
                    audio_new=0,
                    video_new=0,
                    wall_reply_new=0,
                    wall_reply_edit=0,
                    wall_reply_delete=0,
                    wall_reply_restore=0,
                    wall_post_new=0,
                    wall_repost=0,
                    board_post_new=0,
                    board_post_edit=0,
                    board_post_restore=0,
                    board_post_delete=0,
                    photo_comment_new=0,
                    photo_comment_edit=0,
                    photo_comment_delete=0,
                    photo_comment_restore=0,
                    video_comment_new=0,
                    video_comment_edit=0,
                    video_comment_delete=0,
                    video_comment_restore=0,
                    market_comment_new=0,
                    market_comment_edit=0,
                    market_comment_delete=0,
                    market_comment_restore=0,
                    poll_vote_new=0,
                    group_join=0,
                    group_leave=0,
                    group_change_settings=0,
                    group_change_photo=0,
                    group_officers_edit=0,
                    user_block=0,
                    user_unblock=0
                ),
                **self.longpoll_settings
            }
        )

        await self.update_longpoll_data()

        logger.info("logged in as \"{}\" ( https://vk.com/id{} )".format(
            current_group_s.response[0]["name"],
            current_group_s.response[0]["id"]
        ))

        return self.receiver

    async def dispose(self):
        self.running = False

        if self.session:
            await self.session.close()
