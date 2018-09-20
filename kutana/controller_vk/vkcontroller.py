from kutana.controller_vk.vkwrappers import make_reply, make_upload_docs,\
    make_upload_photo
from kutana.controller_vk.converter import convert_to_message
from kutana.controller_basic import BasicController
from kutana.plugin import Attachment
from kutana.logger import logger
from collections import namedtuple
import asyncio
import aiohttp
import json


VKResponse = namedtuple(
    "VKResponse",
    "error errors response"
)

VKResponse.__doc__ = """ `error` is a boolean value indicating if error
happened.

`errors` contains array with happened errors.

`response` contains result of reqeust if no errors happened.
"""


class VKRequest(asyncio.Future):
    __slots__ = ("mthod", "kwargs")

    def __init__(self, method, kwargs):
        super().__init__()

        self.method = method
        self.kwargs = kwargs


class VKController(BasicController):
    """Class for receiving updates from vk.com.
    Controller requires group's token. You can specify settings for
    groups.setLongPollSettings with argument `longpoll_settings`.
    """

    type = "vk"

    def __init__(self, token, execute_pause=0.05, longpoll_settings=None):
        if not token:
            raise ValueError("No `token` specified")

        if not longpoll_settings:
            longpoll_settings = {}

        self.session = None
        self.group_id = None
        self.longpoll = None

        self.subsessions = []

        self.running = True
        self.requests_queue = []

        self.version = "5.80"
        self.token = token
        self.execute_pause = execute_pause
        self.longpoll_settings = longpoll_settings

        self.api_url = "https://api.vk.com/method/{{}}?access_token={}&v={}" \
            .format(self.token, self.version)
        self.longpoll_url = "{}?act=a_check&key={}&wait=25&ts={}"

    async def __aenter__(self):
        self.subsessions.append(self.session)

        self.session = aiohttp.ClientSession()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        if not self.session.closed:

            await self.session.close()

        self.session = self.subsessions.pop(-1)

    async def raw_request(self, method, **kwargs):
        """Perform api request to vk.com"""

        if not self.session:
            self.session = aiohttp.ClientSession()

        url = self.api_url.format(method)

        data = {}

        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

        try:
            async with self.session.post(url, data=data) as response:
                raw_respose_text = await response.text()

                raw_respose = json.loads(raw_respose_text)

        except Exception as e:
            return VKResponse(
                error=True,
                errors=(("Kutana", str(type(e)) + ": " + str(e)),),
                response=""
            )

        if "error" in raw_respose:
            return VKResponse(
                error=True,
                errors=(
                    ("VK_req", raw_respose.get("error","")),
                    ("VK_exe", raw_respose.get("execute_errors", ""))
                ),
                response=raw_respose.get("response", "")
            )

        return VKResponse(
            error=False,
            errors=(
                ("VK_req", raw_respose.get("error","")),
                ("VK_exe", raw_respose.get("execute_errors", ""))
            ),
            response=raw_respose["response"]
        )

    async def request(self, method, **kwargs):
        """Shedule execution of request to vk.com and return result."""

        request = VKRequest(
            method,
            kwargs
        )

        self.requests_queue.append(request)

        await request

        try:
            return await asyncio.wait_for(request, timeout=10)

        except asyncio.TimeoutError:
            return VKResponse(
                error=True,
                errors=(
                    ("Kutana", "Request took too long and was forgotten.")
                ),
                response=""
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
        )

    async def setup_env(self, update, eenv):
        peer_id = update["object"].get("peer_id")

        if update["type"] == "message_new":
            eenv["reply"] = make_reply(self, peer_id)

        eenv["send_message"] = self.send_message

        eenv["upload_photo"] = make_upload_photo(self, peer_id)
        eenv["upload_doc"] = make_upload_docs(self, peer_id)

        eenv["request"] = self.request

    async def convert_to_message(self, update, eenv):
        return await convert_to_message(update, eenv)

    @staticmethod
    async def _set_results_to_requests(result, requests):
        err_no = 0

        if result.errors and result.errors[-1][0] == "VK_exe":
            execute_errors = result.errors[-1][1]

        else:
            execute_errors = []

        for res, req in zip(result.response, requests):
            if res is False:
                if len(execute_errors) > err_no:
                    known_error = execute_errors[err_no]
                    err_no += 1

                else:
                    known_error = ""

                res = VKResponse(
                    error=True,
                    errors=(("VK_req", known_error),),
                    response=""
                )

            else:
                res = VKResponse(
                    error=False,
                    errors=(),
                    response=res
                )

            try:
                req.set_result(res)
            except asyncio.InvalidStateError:
                pass

    async def _msg_exec_loop(self, ensure_future):
        while self.running:
            await asyncio.sleep(self.execute_pause)

            requests = []

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
                logger.error(result.errors)

            await ensure_future(self._set_results_to_requests(result, requests))

    async def get_background_coroutines(self, ensure_future):
        return (self._msg_exec_loop(ensure_future),)

    async def update_longpoll_data(self):
        longpoll = await self.raw_request("groups.getLongPollServer", group_id=self.group_id)

        if longpoll.error:
            raise ValueError(
                "Couldn't get longpoll information\n{}"
                .format(
                    longpoll.errors
                )
            )

        self.longpoll = {
            **longpoll.response
        }

    async def receiver(self):
        try:
            async with self.session.post(
                self.longpoll_url.format(
                    self.longpoll["server"],
                    self.longpoll["key"],
                    self.longpoll["ts"],
                )
            ) as resp:
                response = await resp.json()

        except Exception:
            return []

        if "ts" in response:
            self.longpoll["ts"] = response["ts"]

        if "failed" in response:
            if response["failed"] in (2, 3, 4):
                await self.update_longpoll_data()

            return []

        updates = []

        for update in response["updates"]:
            if "type" not in update or "object" not in update:
                continue

            updates.append(update)

        return updates

    async def get_receiver_coroutine_function(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

        current_group_s = await self.raw_request("groups.getById")

        if current_group_s.error or not current_group_s.response[0].get("id"):
            raise ValueError(
                "Couldn't get group information\n{}"
                .format(
                    current_group_s.errors
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
                    message_new=1,
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

        logger.info("logged in as \"{}\" ( https://vk.com/club{} )".format(
            current_group_s.response[0]["name"],
            current_group_s.response[0]["id"]
        ))

        return self.receiver

    async def dispose(self):
        self.running = False

        if self.session:
            await self.session.close()
