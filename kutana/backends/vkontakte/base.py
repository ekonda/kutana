import asyncio
import json
import logging
import re
from functools import partial
from itertools import zip_longest
from random import random

from kutana.helpers import create_httpx_async_client

from ...backend import Backend
from ...exceptions import RequestException
from ...update import Attachment, AttachmentKind, Message, RecipientKind

DEFAULT_RECEIVABLE_EVENTS = {
    "message_new": 1,
    "message_reply": 0,
    "message_edit": 1,
    "message_allow": 0,
    "message_deny": 0,
    "photo_new": 0,
    "audio_new": 0,
    "video_new": 0,
    "wall_reply_new": 0,
    "wall_reply_edit": 0,
    "wall_reply_delete": 0,
    "wall_post_new": 0,
    "wall_repost": 0,
    "board_post_new": 0,
    "board_post_edit": 0,
    "board_post_delete": 0,
    "board_post_restore": 0,
    "photo_comment_new": 0,
    "photo_comment_edit": 0,
    "photo_comment_delete": 0,
    "photo_comment_restore": 0,
    "video_comment_new": 0,
    "video_comment_edit": 0,
    "video_comment_delete": 0,
    "video_comment_restore": 0,
    "market_comment_new": 0,
    "market_comment_edit": 0,
    "market_comment_delete": 0,
    "market_comment_restore": 0,
    "poll_vote_new": 0,
    "group_join": 0,
    "group_leave": 0,
    "user_block": 0,
    "user_unblock": 0,
    "group_change_settings": 1,
    "group_change_photo": 0,
    "group_officers_edit": 0,
    "donut_subscription_create": 0,
    "donut_subscription_prolonged": 0,
    "donut_subscription_expired": 0,
    "donut_subscription_cancelled": 0,
    "subscription_price_changed": 0,
    "donut_money_withdraw": 0,
    "donut_money_withdraw_error": 0,
}


class Vkontakte(Backend):
    def __init__(
        self,
        token,
        requests_per_second=19,
        api_version="5.131",
        api_url="https://api.vk.com",
    ):
        if not token:
            raise ValueError("No token provided for backend")

        self.api_token = token
        self.api_version = api_version
        self.api_request_pause = 1 / requests_per_second

        self.client = create_httpx_async_client()

        self.group: dict
        self.requests_queue: asyncio.Queue
        self.requests_queue_handler: asyncio.Task

        self.api_request_url = api_url + f"/method/{{}}?access_token={token}&v={api_version}"

    def get_identity(self):
        return "vk"

    async def _resolve_screen_name(self, screen_name, cache={}):
        if cache and screen_name in cache:
            return cache[screen_name]

        response = await self._direct_request("utils.resolveScreenName", {"screen_name": screen_name})

        if response and isinstance(cache, dict):
            if len(cache) > 65536:
                cache.clear()
            cache[screen_name] = response

        return response

    async def setup_context(self, context):
        context.resolve_screen_name = self._resolve_screen_name

    def _extract_text(self, text):
        bot_mention_regex = r"\[((public|club){}|{})\|.+\]".format(
            re.escape(str(self.group["id"])),
            re.escape(self.group["screen_name"]),
        )

        return re.sub(bot_mention_regex, "", text).lstrip()

    async def _get_file(self, url):
        response = await self.client.get(url)
        return response.content

    @staticmethod
    def _make_attachment_full_id(raw_attachment_type, raw_attachment_media):
        full_id_postfix = "_".join(
            filter(
                None,
                map(
                    str,
                    [
                        raw_attachment_media.get("owner_id"),
                        raw_attachment_media.get("id"),
                        raw_attachment_media.get("access_key"),
                    ],
                ),
            )
        )

        if not full_id_postfix:
            return None

        return f"{raw_attachment_type}{full_id_postfix}"

    def _make_attachment(self, raw_attachment):
        raw_attachment_media = raw_attachment[raw_attachment["type"]]

        full_id = self._make_attachment_full_id(raw_attachment["type"], raw_attachment_media)

        if raw_attachment["type"] == "audio":
            return Attachment(
                id=full_id,
                kind=AttachmentKind.AUDIO,
                title=f"{raw_attachment_media['artist']} - {raw_attachment_media['title']}",
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment_media["url"]),
            )

        if raw_attachment["type"] == "doc":
            return Attachment(
                id=full_id,
                kind=AttachmentKind.DOCUMENT,
                title=raw_attachment_media["title"],
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment_media["url"]),
            )

        if raw_attachment["type"] == "photo":
            largest_size = list(sorted(raw_attachment_media["sizes"], key=lambda size: size["width"]))[0]
            return Attachment(
                id=full_id,
                kind=AttachmentKind.IMAGE,
                raw=raw_attachment,
                get_file=partial(self._get_file, largest_size["url"]),
            )

        if raw_attachment["type"] == "video":
            return Attachment(
                id=full_id,
                kind=AttachmentKind.VIDEO,
                raw=raw_attachment,
                get_file=None,
            )

        if raw_attachment["type"] == "audio_message":
            return Attachment(
                id=full_id,
                kind=AttachmentKind.VOICE,
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment_media["link_mp3"]),
            )

        return Attachment(
            id=full_id,
            kind=raw_attachment["type"],
            raw=raw_attachment,
        )

    def _make_update(self, raw_update):
        if raw_update["type"] != "message_new":
            return raw_update

        message = raw_update["object"]["message"]

        attachments = []

        for attachment in message["attachments"]:
            attachments.append(self._make_attachment(attachment))

        if message["peer_id"] > 2000000000:
            recipient_kind = RecipientKind.GROUP_CHAT
        else:
            recipient_kind = RecipientKind.PRIVATE_CHAT

        return Message(
            sender_id=message["from_id"],
            recipient_id=message["peer_id"],
            recipient_kind=recipient_kind,
            text=self._extract_text(raw_update["object"]["message"]["text"]),
            attachments=attachments,
            date=message["date"],
            raw=raw_update,
        )

    async def _update_group_data(self):
        groups = await self._direct_request("groups.getById", {"fields": "screen_name"})

        self.group = groups[0]

    async def on_start(self, app):
        await self._update_group_data()

        logging.info(
            'logged in as "%s" ( https://vk.com/club%s )',
            self.group["name"],
            self.group["id"],
        )

        self.requests_queue = asyncio.Queue()

        self.requests_queue_handler = asyncio.ensure_future(self._handle_requests_queue())

    async def _direct_request(self, method, kwargs):
        response = await self.client.post(
            self.api_request_url.format(method),
            data={k: v for k, v in kwargs.items() if v is not None},
        )

        try:
            data = response.json()
        except Exception as exception:
            raise RequestException(
                self,
                method,
                kwargs,
                response.content,
                exception=exception,
            )

        if data.get("response") is None:
            raise RequestException(self, method, kwargs, data)

        return data["response"]

    async def _handle_requests_queue(self):
        while True:
            await asyncio.sleep(self.api_request_pause)

            requests_chunk = []

            for _ in range(25):
                try:
                    requests_chunk.append(self.requests_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            if not requests_chunk:
                continue

            asyncio.ensure_future(self._handle_requests_chunk(requests_chunk))

    async def _handle_requests_chunk(self, chunk):
        code = "return ["

        for method, kwargs, _ in chunk:
            serialized_kwargs = json.dumps(kwargs, separators=(",", ":"), ensure_ascii=False)
            code += f"API.{method}({serialized_kwargs}),"

        code += "];"

        response = await self._direct_request("execute", {"code": code})

        for result, (method, kwargs, future) in zip_longest(response, chunk):
            if future.done():
                continue

            if result is not None:
                future.set_result(result)
                continue

            future.set_exception(
                RequestException(
                    self,
                    method,
                    kwargs,
                    result,
                ),
            )

    async def request(self, method, kwargs):
        future = asyncio.Future()
        await self.requests_queue.put((method, kwargs, future))
        return await future

    async def upload_attachment(self, attachment, peer_id):
        if attachment.kind == AttachmentKind.IMAGE:
            upload_data = await self.request(
                "photos.getMessagesUploadServer",
                {"peer_id": peer_id},
            )

            upload_response = await self.client.post(
                upload_data["upload_url"],
                files={"photo": attachment.content},
            )

            result = await self.request(
                "photos.saveMessagesPhoto",
                upload_response.json(),
            )

            return f'photo{result[0]["owner_id"]}_{result[0]["id"]}'

        if attachment.kind in (AttachmentKind.DOCUMENT, AttachmentKind.VOICE):
            vk_type = "audio_message" if attachment.kind == AttachmentKind.VOICE else "doc"

            upload_data = await self.request(
                "docs.getMessagesUploadServer",
                {"peer_id": peer_id, "type": vk_type},
            )

            upload_response = await self.client.post(
                upload_data["upload_url"],
                files={"file": attachment.content},
            )

            result = await self.request(
                "docs.save",
                upload_response.json(),
            )

            return f'{vk_type}{result[vk_type]["owner_id"]}_{result[vk_type]["id"]}'

        raise ValueError(f'Unsupported attachment kind: "{attachment.kind}"')

    async def send_message(self, recipient_id, text=None, attachments=None, **kwargs):
        formatted_attachments = []

        if attachments:
            for attachment in attachments:
                if isinstance(attachment, str):
                    formatted_attachments.append(attachment)
                    continue

                if attachment.id:
                    formatted_attachments.append(attachment.id)
                    continue

                formatted_attachments.append(
                    await self.upload_attachment(attachment, peer_id=recipient_id),
                )

        return await self.request(
            "messages.send",
            {
                "peer_id": recipient_id,
                "message": str(text),
                "attachment": ",".join(formatted_attachments),
                **kwargs,
                "random_id": kwargs.get("random_id") or int(random() * 4294967296) - 2147483648,
            },
        )

    async def on_shutdown(self, app):
        self.requests_queue_handler.cancel()
        await self.client.aclose()
