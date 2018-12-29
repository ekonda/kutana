"""Manager for interacting with VKontakte"""

import asyncio
import json
import re
from collections import namedtuple

import aiohttp
from kutana.logger import logger
from kutana.manager.basic import BasicManager
from kutana.manager.vk.environment import VKEnvironment
from kutana.plugin import Attachment, Message


NAIVE_CACHE = {}


VKResponse = namedtuple(
    "VKResponse",
    "error errors response"
)

VKResponse.__doc__ = """
"error" is a boolean value indicating if errorhappened.
"errors" contains array with happened errors.
"response" contains result of reqeust if no errors happened.
"""


class VKRequest(asyncio.Future):
    """Class for queueing requests to VKontakte"""

    def __init__(self, method, kwargs):
        super().__init__()

        self.method = method
        self.kwargs = kwargs


class VKManager(BasicManager):
    """
    Class for receiving updates from vkontakte.
    Controller requires group's token. You can specify settings for
    groups.setLongPollSettings with argument "longpoll_settings".
    """


    type = "vkontakte"


    def __init__(self, token, execute_pause=0.05, longpoll_settings=None):
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
        self.execute_pause = execute_pause
        self.longpoll_settings = longpoll_settings

        self.api_url = "https://api.vk.com/method/{{}}?access_token={}&v={}" \
            .format(self.token, self.version)
        self.longpoll_url = "{}?act=a_check&key={}&wait=25&ts={}"

    async def raw_request(self, method, **kwargs):
        """Perform raw api request to vkontakte"""

        if not self.session:
            self.session = aiohttp.ClientSession()

        data = {k: v for k, v in kwargs.items() if v is not None}

        try:
            async with self.session.post(
                    self.api_url.format(method),
                    data=data
                ) as response:

                raw_respose_text = await response.text()

                raw_respose = json.loads(raw_respose_text)

        except (json.JSONDecodeError, aiohttp.ClientError) as e:
            return VKResponse(
                error=True,
                errors=(("Kutana", str(type(e)) + ": " + str(e)),),
                response=""
            )

        if "error" in raw_respose:
            return VKResponse(
                error=True,
                errors=(
                    ("VK_req", raw_respose.get("error", "")),
                    ("VK_exe", raw_respose.get("execute_errors", ""))
                ),
                response=raw_respose.get("response", "")
            )

        return VKResponse(
            error=False,
            errors=(
                ("VK_req", raw_respose.get("error", "")),
                ("VK_exe", raw_respose.get("execute_errors", ""))
            ),
            response=raw_respose["response"]
        )

    async def request(self, method, **kwargs):
        """
        Perform request to vkontakte and return result.

        :param method: method to call
        :param timeout: timeout for gettings response from vkontakte
        :param kwargs: parameters for method
        :rtype: :class:`.VKResponse`
        """

        timeout = kwargs.pop("_timeout", 30)

        req = VKRequest(
            method,
            kwargs
        )

        self.requests_queue.append(req)

        try:
            return await asyncio.wait_for(req, timeout=timeout)

        except asyncio.TimeoutError:
            return VKResponse(
                error=True,
                errors=(
                    ("Kutana", "Request took too long and was forgotten.")
                ),
                response=""
            )

    async def send_message(self, message, peer_id, attachment=None, **kwargs):
        """
        Send message to target peer_id with parameters.

        :param message: text to send
        :param peer_id: target recipient
        :param attachment: list of :class:`.Attachment` or attachments
            as string
        :parma kwargs: arguments to send to vkontakte's `messages.send`
        :rtype: list of responses from telegram
        """

        if peer_id is None:
            return ()

        message_parts = self.split_large_text(message)

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

        result = []

        for part in message_parts[:-1]:
            result.append(
                await self.request(
                    "messages.send",
                    message=part,
                    peer_id=peer_id
                )
            )

        result.append(
            await self.request(
                "messages.send",
                message=message_parts[-1],
                peer_id=peer_id,
                attachment=attachment,
                **kwargs
            )
        )

        return result

    async def resolve_screen_name(self, screen_name):
        """Return answer from vkontakte with resolved passed screen name."""

        if screen_name in NAIVE_CACHE:
            return NAIVE_CACHE[screen_name]

        result = await self.request(
            "utils.resolveScreenName",
            screen_name=screen_name
        )

        NAIVE_CACHE[screen_name] = result

        return result

    async def create_message(self, update):
        if update["type"] != "message_new":
            return None

        obj = update["object"]

        text = obj["text"]

        if "conversation_message_id" in obj:
            cursor = 0
            new_text = ""

            for match in re.finditer(r"\[(.+?)\|.+?\]", text):
                resp = await self.resolve_screen_name(match.group(1))

                new_text += text[cursor : match.start()]

                cursor = match.end()

                if not resp.response or resp.response["object_id"] == update["group_id"]:
                    continue

                new_text += text[match.start() : match.end()]

            new_text += text[cursor :]

            text = new_text.lstrip()

        return Message(
            text,
            tuple(self.create_attachment(a) for a in obj["attachments"]),
            obj.get("from_id"),
            obj.get("peer_id"),
            obj.get("date"),
            update
        )

    @staticmethod
    def create_attachment(attachment, attachment_type=None):
        """
        Create and return :class:`.Attachment` created from passed data. If
        attachment type can't be determined passed "attachment_type"
        well be used.
        """

        if "type" in attachment and attachment["type"] in attachment:
            body = attachment[attachment["type"]]
            attachment_type = attachment["type"]
        else:
            body = attachment

        if "sizes" in body:
            m_s_ind = -1
            m_s_wid = 0

            for i, size in enumerate(body["sizes"]):
                if size["width"] >= m_s_wid:
                    m_s_wid = size["width"]
                    m_s_ind = i

            link = body["sizes"][m_s_ind]["url"]  # src

        elif "url" in body:
            link = body["url"]

        else:
            link = None

        return Attachment(
            attachment_type,
            body.get("id"),
            body.get("owner_id"),
            body.get("access_key"),
            link,
            attachment
        )

    async def get_environment(self, update):
        """
        Returns environment for update.

        :param update: update from vkontakte
        :rtype: :class:`.VKEnvironment`
        """

        return VKEnvironment(self, peer_id=update["object"].get("peer_id"))

    @staticmethod
    def _set_results_to_requests(result, requests):
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

    async def _msg_exec_loop(self, _):
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

            self._set_results_to_requests(result, requests)

    async def get_background_coroutines(self, ensure_future):
        return (self._msg_exec_loop(ensure_future),)

    async def update_longpoll_data(self):
        """Update manager's longpoll data"""

        longpoll = await self.raw_request(
            "groups.getLongPollServer", group_id=self.group_id
        )

        if longpoll.error:
            raise ValueError(
                "Couldn't get longpoll information\n{}".format(
                    longpoll.errors
                )
            )

        self.longpoll = {
            **longpoll.response
        }

    async def receiver(self):
        """Return new updates for bot from vkontakte."""

        try:
            async with self.session.post(
                    self.longpoll_url.format(
                        self.longpoll["server"],
                        self.longpoll["key"],
                        self.longpoll["ts"],
                    )
            ) as resp:
                response = await resp.json()

        except (json.JSONDecodeError, aiohttp.ClientError):
            return ()

        if "ts" in response:
            self.longpoll["ts"] = response["ts"]

        if "failed" in response:
            if response["failed"] in (2, 3, 4):
                await self.update_longpoll_data()

            return ()

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

        logger.info(
            "logged in as \"%s\" ( https://vk.com/club%s )",
            current_group_s.response[0]["name"],
            current_group_s.response[0]["id"]
        )

        return self.receiver

    async def dispose(self):
        self.running = False

        if self.session:
            await self.session.close()
