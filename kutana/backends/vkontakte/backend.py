from random import random
import asyncio
import json
import re
import aiohttp
from ...logger import logger
from ...backend import Backend
from ...update import (
    ReceiverType, UpdateType, Update, Message, Attachment,
)
from ...exceptions import RequestException


NAIVE_CACHE = {}


class VKRequest(asyncio.Future):
    def __init__(self, method, kwargs):
        super().__init__()
        self.method = method
        self.kwargs = kwargs


class Vkontakte(Backend):
    def __init__(
        self,
        token,
        session=None,
        requests_per_second=19,
        longpoll_settings=None,
        api_version="5.103",
        api_url="https://api.vk.com"
    ):
        if not token:
            raise ValueError("No `token` specified")

        self.api_token = token
        self.api_version = api_version
        self.api_request_pause = 1 / requests_per_second

        self.session = session
        self._is_session_local = session is None

        self.group_id = None
        self.group_screen_name = None
        self.group_name = None

        self.longpoll_settings = longpoll_settings or {}
        self.longpoll_data = None

        self.requests_queue = []

        self.api_request_url = api_url + f"/method/{{}}?access_token={token}&v={api_version}"

        self.longpoll_url_template = "{}?act=a_check&key={}&wait=25&ts={}"

    async def _get_response(self, method, kwargs={}):
        data = {k: v for k, v in kwargs.items() if v is not None}

        request_url = self.api_request_url.format(method)

        async with self.session.post(request_url, data=data) as response:
            return await response.json(content_type=None)

    async def raw_request(self, method, kwargs={}):
        """
        Call specified method from VKontakte api with specified kwargs
        and return response's data.

        This method raises RequestException if response contains error.
        """

        data = await self._get_response(method, kwargs)

        if not data.get("response"):
            raise RequestException(self, (method, {**kwargs}), data)

        return data["response"]

    async def _execute_loop(self, loop):
        while True:
            await asyncio.sleep(self.api_request_pause)

            requests = []

            for _ in range(25):
                if not self.requests_queue:
                    break

                requests.append(self.requests_queue.pop())

            if not requests:
                continue

            code = "return ["

            for r in requests:
                kwargs = json.dumps(r.kwargs, ensure_ascii=False)
                code += f"API.{r.method}({kwargs}),"

            code += "];"

            asyncio.ensure_future(
                self._execute_loop_perform_execute(code, requests),
                loop=loop,
            )

    async def _execute_loop_perform_execute(self, code, requests):
        response = await self._get_response("execute", {"code": code})

        result = response.get("response") or []
        errors = response.get("execute_errors") or []

        if len(result) != len(requests):
            result = [*result, *[False] * (len(requests) - len(result))]

        if len(errors) != len(requests):
            errors = [*errors, *[None] * (len(requests) - len(errors))]

        for res, req, err in zip(result, requests, errors):
            if req.done():
                continue

            if res is False or res is None:
                req.set_exception(RequestException(
                    self,
                    (req.method, req.kwargs),
                    res,
                    err,
                ))
            else:
                req.set_result(res)

    async def _request(self, method, kwargs, timeout=None):
        req = VKRequest(method, kwargs)

        self.requests_queue.append(req)

        res = await asyncio.wait_for(req, timeout=timeout)

        logger.debug("Vkontakte: %s(%s) => %s", method, kwargs, res)

        return res

    async def update_longpoll_data(self):
        longpoll = await self.raw_request(
            "groups.getLongPollServer", {"group_id": self.group_id}
        )

        self.longpoll_data = longpoll.copy()

    async def resolve_screen_name(self, screen_name):
        if screen_name in NAIVE_CACHE:
            return NAIVE_CACHE[screen_name]

        result = await self._request(
            "utils.resolveScreenName",
            {"screen_name": screen_name}
        )

        if not result:
            return {}

        if len(NAIVE_CACHE) >= 500_000:
            NAIVE_CACHE.clear()

        NAIVE_CACHE[screen_name] = result

        return result

    async def _update_group_data(self):
        groups = await self.raw_request("groups.getById", {
            "fields": "screen_name"
        })

        self.group_id = groups[0]["id"]
        self.group_name = groups[0]["name"]
        self.group_screen_name = groups[0]["screen_name"]

    def prepare_context(self, ctx):
        ctx.resolve_screen_name = self.resolve_screen_name

    def _make_getter(self, url):
        async def getter():
            async with self.session.get(url) as response:
                return await response.read()
        return getter

    def _make_attachment(self, raw_attachment):
        t = raw_attachment["type"]
        d = raw_attachment[t]

        if "owner_id" in d and "id" in d:
            id = f"{t}{d['owner_id']}_{d['id']}"
        else:
            id = None

        if t == "photo":
            return Attachment._existing_full(
                id=id, type="image", title=d["text"], file_name=id,
                getter=self._make_getter(d["sizes"][-1]["url"]), raw=d,
            )

        elif t == "doc":
            return Attachment._existing_full(
                id=id, type="doc", title=d.get("title", ""), file_name=id,
                getter=self._make_getter(d["url"]), raw=d,
            )

        elif t == "audio_message":
            return Attachment._existing_full(
                id=id, type="voice", title="", file_name=id,
                getter=self._make_getter(d["link_mp3"]), raw=d,
            )

        elif t == "sticker":
            id = f"{d['sticker_id']}"
            url = list(sorted(d["images"], key=lambda i: i["width"]))[-1]

            return Attachment._existing_full(
                id=id, type="sticker", title="", file_name=id,
                getter=self._make_getter(url), raw=d,
            )

        elif t == "audio":
            return Attachment._existing_full(
                id=id, type="audio", title=d["artist"] + " - " + d["title"],
                file_name=id, getter=self._make_getter(d["url"]), raw=d,
            )

        elif t == "video":
            return Attachment._existing_full(
                id=id, type="video", title=d["title"], file_name=id,
                getter=None, raw=d,
            )

        else:
            return Attachment._existing_full(
                id=id, type=t, title=None, file_name=None, getter=None,
                raw=d,
            )

    def _make_update(self, raw_update):
        raw_update_type = raw_update["type"]
        raw_update_object = raw_update["object"]

        if raw_update_type != "message_new":
            return Update(raw_update, UpdateType.UPD)

        raw_message = raw_update_object["message"]

        message_text = raw_message["text"]

        if raw_message["peer_id"] > 2000000000:
            receiver_type = ReceiverType.MULTI

            def sub(match):
                possible_ids = (
                    f"club{self.group_id}",
                    f"public{self.group_id}",
                    self.group_screen_name,
                )

                if match.group(1) in possible_ids:
                    return ""
                else:
                    return match.group(0)

            message_text = re.sub(r"\[(.+?)\|.+?\]", sub, message_text)
            message_text = message_text.lstrip()
        else:
            receiver_type = ReceiverType.SOLO

        attachments = []

        for attachment in raw_message.get("attachments") or ():
            attachments.append(self._make_attachment(attachment))

        return Message(
            raw=raw_update,
            type=UpdateType.MSG,
            text=message_text,
            attachments=attachments,
            sender_id=raw_message["from_id"],
            receiver_id=raw_message["peer_id"],
            receiver_type=receiver_type,
            date=raw_message["date"],
        )

    async def _upload_file_to_vk(self, upload_url, data):
        async with self.session.post(upload_url, data=data) as resp:
            return await resp.json(content_type=None)

    async def upload_attachment(self, attachment, peer_id=None):
        """
        Upload specified attachment to VKontakte with specified peer_id and
        return newly uploaded attachment.

        This method doesn't change passed attachments.
        """

        attachment_type = attachment.type

        if attachment_type == "voice":
            attachment_type = "doc"
            doctype = "audio_message"
        elif attachment_type == "graffiti":
            attachment_type = "doc"
            doctype = "graffiti"
        else:
            doctype = "doc"

        if attachment_type == "doc":
            if peer_id and doctype != "graffiti":
                upload_data = await self._request(
                    "docs.getMessagesUploadServer",
                    {"peer_id": peer_id, "type": doctype},
                )
            else:
                upload_data = await self._request(
                    "docs.getWallUploadServer",
                    {"group_id": self.group_id, "type": doctype},
                )

            data = aiohttp.FormData()
            data.add_field(
                "file", attachment.file, filename=attachment.file_name,
            )

            upload_result = await self._upload_file_to_vk(
                upload_data["upload_url"], data
            )

            attachment = await self._request(
                "docs.save", upload_result
            )

            return self._make_attachment(attachment)

        if attachment_type == "image":
            upload_data = await self._request(
                "photos.getMessagesUploadServer", {"peer_id": peer_id}
            )

            data = aiohttp.FormData()
            data.add_field(
                "photo", attachment.file, filename=attachment.file_name
            )

            upload_result = await self._upload_file_to_vk(
                upload_data["upload_url"], data
            )

            try:
                attachments = await self._request(
                    "photos.saveMessagesPhoto", upload_result
                )
            except RequestException as e:
                if not peer_id or not e.error or e.error["error_code"] != 1:
                    raise

                return await self.upload_attachment(attachment, peer_id=None)

            return self._make_attachment({
                "type": "photo",
                "photo": attachments[0],
            })

        raise ValueError(f"Can't upload attachment '{attachment_type}'")

    async def _get_updates(self):
        longpoll_url = self.longpoll_url_template.format(
            self.longpoll_data["server"],
            self.longpoll_data["key"],
            self.longpoll_data["ts"],
        )

        try:
            async with self.session.post(longpoll_url) as resp:
                return await resp.json(content_type=None)

        except (json.JSONDecodeError, aiohttp.ClientError):
            return None

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Exceptions while gettings updates (Vkontakte)")
            await asyncio.sleep(1)
            return None

    async def perform_updates_request(self, submit_update):
        response = await self._get_updates()

        if response is None:
            return

        if "ts" in response:
            self.longpoll_data["ts"] = response["ts"]

        if "failed" in response:
            if response["failed"] in (2, 3):
                await self.update_longpoll_data()
            return

        for update_data in response["updates"]:
            if "type" not in update_data or "object" not in update_data:
                continue

            if update_data["type"] == "group_change_settings":
                changes = update_data["object"]["changes"]

                screen_name = changes.get("screen_name")
                if screen_name:
                    self.group_screen_name = screen_name["new_value"]

                title = changes.get("title")
                if title:
                    self.group_name = title["new_value"]

            update = self._make_update(update_data)

            await submit_update(update)

    async def perform_send(self, target_id, message, attachments, kwargs):
        # Form proper arguments
        true_kwargs = {"message": message, "peer_id": target_id}
        true_kwargs.update(kwargs)

        if "random_id" not in kwargs:
            true_kwargs["random_id"] = int(random() * 4294967296) - 2147483648

        # Form proper attachments
        true_attachments = ""

        if isinstance(attachments, (int, str, Attachment)):
            attachments = (attachments,)

        for a in attachments:
            if isinstance(a, Attachment):
                if a.type == "sticker":
                    true_kwargs["sticker_id"] = a.id
                    continue

                if not a.uploaded:
                    a = await self.upload_attachment(a, peer_id=target_id)

                if not a.id:
                    raise ValueError("Attachment has no ID")

                true_attachments += f"{a.id}"

                access_key = (a.raw or {}).get("access_key")
                if access_key:
                    true_attachments += "_" + access_key

            else:
                true_attachments += str(a)

            true_attachments += ","

        # Add attachments to arguments
        if true_attachments[:-1]:
            true_kwargs["attachment"] = true_attachments[:-1]

        return await self._request("messages.send", true_kwargs)

    async def perform_api_call(self, method, kwargs):
        return await self._request(method, kwargs)

    async def on_start(self, app):
        if not self.session:
            self.session = aiohttp.ClientSession()

        await self._update_group_data()

        longpoll_settings = dict(
            message_new=1, message_reply=0, message_allow=0,
            message_deny=0, message_edit=0, photo_new=0, audio_new=0,
            video_new=0, wall_reply_new=0, wall_reply_edit=0,
            wall_reply_delete=0, wall_reply_restore=0, wall_post_new=0,
            wall_repost=0, board_post_new=0, board_post_edit=0,
            board_post_restore=0, board_post_delete=0, photo_comment_new=0,
            photo_comment_edit=0, photo_comment_delete=0,
            photo_comment_restore=0, video_comment_new=0,
            video_comment_edit=0, video_comment_delete=0,
            video_comment_restore=0, market_comment_new=0,
            market_comment_edit=0, market_comment_delete=0,
            market_comment_restore=0, poll_vote_new=0, group_join=0,
            group_leave=0, group_change_settings=1, group_change_photo=0,
            group_officers_edit=0, user_block=0, user_unblock=0
        )

        longpoll_settings.update(self.longpoll_settings)

        await self.raw_request(
            "groups.setLongPollSettings",
            {
                "group_id": self.group_id,
                "api_version": self.api_version,
                "enabled": 1,
                **longpoll_settings,
            }
        )

        await self.update_longpoll_data()

        logger.info(
            'logged in as "%s" ( https://vk.com/club%s )',
            self.group_name,
            self.group_id,
        )

        loop = app.get_loop()

        asyncio.ensure_future(
            self._execute_loop(loop),
            loop=loop
        )

    async def send_message(self, target_id, message, attachments=(), **kwargs):
        """
        Send message to specified `target_id` with text `message` and
        attachments `attachments`.

        This method will forward all excessive keyword arguments to
        sending method.
        """

        return await self.perform_send(target_id, message, attachments, kwargs)

    async def request(self, method, _timeout=None, **kwargs):
        """
        Call specified method from VKontakte api with specified
        kwargs and return response's data.

        This method respects limits.

        This method raises RequestException if response
        contains error.
        """

        return await self._request(method, kwargs, _timeout)

    async def on_shutdown(self, app):
        if self._is_session_local:
            await self.session.close()
