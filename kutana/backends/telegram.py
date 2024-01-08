import asyncio
import io
import json
import logging
from functools import partial

from ..backend import Backend
from ..exceptions import RequestException
from ..helpers import create_httpx_async_client, pick_by
from ..update import Attachment, AttachmentKind, Message, RecipientKind

SUPPORTED_ATTACHMENT_KINDS = {
    AttachmentKind.AUDIO: ("sendAudio", "audio"),
    AttachmentKind.DOCUMENT: ("sendDocument", "document"),
    AttachmentKind.IMAGE: ("sendPhoto", "photo"),
    AttachmentKind.VIDEO: ("sendVideo", "video"),
    AttachmentKind.VOICE: ("sendVoice", "voice"),
}

TELEGRAM_POSSIBLE_ATTACHMENT_KINDS = [
    "audio",
    "contact",
    "document",
    "invoice",
    "location",
    "passport_data",
    "photo",
    "poll",
    "sticker",
    "video_note",
    "video",
    "voice",
]


class Telegram(Backend):
    def __init__(
        self,
        token,
        messages_per_second=29,
        api_url="https://api.telegram.org",
        **kwargs,
    ):
        super().__init__(**kwargs)

        if not token:
            raise ValueError("No token provided for backend")

        self.client = create_httpx_async_client()

        self.username = None
        self.api_token = token
        self.api_messages_pause = 1 / messages_per_second
        self.api_messages_lock: asyncio.Lock

        api_url = api_url.rstrip("/")
        self.api_url = f"{api_url}/bot{token}/{{}}"
        self.file_url = f"{api_url}/file/bot{token}/{{}}"

    def get_identity(self):
        return "tg"

    async def setup_context(self, context):
        if isinstance(context.update, dict):
            if context.update.get("callback_query"):
                context.sender_id = context.update["callback_query"]["from"]["id"]
                context.recipient_id = context.update["callback_query"]["message"][
                    "chat"
                ]["id"]

    async def on_start(self, app):
        me = await self.request("getMe", {})

        name = me.get("first_name", "") + " " + me.get("last_name", "")
        name = name.strip() or "(unknown)"

        logging.info('logged in as "%s" ( https://t.me/%s )', name, me["username"])

        self.username = me["username"]

        self.api_messages_lock = asyncio.Lock()

    def _is_file_like_value(self, value):
        if isinstance(value, (io.IOBase, bytes)):
            return True

        if (
            isinstance(value, tuple)
            and len(value) == 2
            and isinstance(value[1], (io.IOBase, bytes))
        ):
            return True

        return False

    async def request(self, method, kwargs):
        data = {}
        files = {}

        for key, value in kwargs.items():
            if value is None:
                continue

            if self._is_file_like_value(value):
                files[key] = value
            elif isinstance(value, (list, dict)):
                data[key] = json.dumps(value)
            else:
                data[key] = value

        response = await self.client.post(
            self.api_url.format(method),
            data=data,
            files=files,
            timeout=60,
        )

        response_data = response.json()

        if not response_data.get("ok"):
            raise RequestException(self, method, kwargs, response_data)

        return response_data["result"]

    async def _get_file(self, file_id):
        file = await self.request("getFile", {"file_id": file_id})
        response = await self.client.get(self.file_url.format(file["file_path"]))
        return response.content

    def _make_attachment(self, raw_attachment, raw_attachment_kind):
        if raw_attachment_kind == "audio":
            return Attachment(
                id=raw_attachment["file_id"],
                kind=AttachmentKind.AUDIO,
                title=raw_attachment["title"],
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment["file_id"]),
            )

        if raw_attachment_kind == "document":
            return Attachment(
                id=raw_attachment["file_id"],
                kind=AttachmentKind.DOCUMENT,
                title=raw_attachment.get("file_name"),
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment["file_id"]),
            )

        if raw_attachment_kind == "photo":
            largest_photo = list(
                sorted(raw_attachment, key=lambda photo: photo["width"])
            )[0]
            return Attachment(
                id=largest_photo["file_id"],
                kind=AttachmentKind.IMAGE,
                raw=raw_attachment,
                get_file=partial(self._get_file, largest_photo["file_id"]),
            )

        if raw_attachment_kind == "video":
            return Attachment(
                id=raw_attachment["file_id"],
                kind=AttachmentKind.VIDEO,
                title=raw_attachment.get("file_name"),
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment["file_id"]),
            )

        if raw_attachment_kind == "voice":
            return Attachment(
                id=raw_attachment["file_id"],
                kind=AttachmentKind.VOICE,
                raw=raw_attachment,
                get_file=partial(self._get_file, raw_attachment["file_id"]),
            )

        return Attachment(
            id=raw_attachment.get("file_id"),
            kind=raw_attachment_kind,
            raw=raw_attachment,
        )

    def _extract_text(self, update):
        if not update["message"].get("entities"):
            return update["message"].get("text")

        original_text = update["message"]["text"]
        text = ""
        processed_index = 0

        for entity in update["message"]["entities"]:
            if entity["type"] != "bot_command":
                continue

            text += original_text[processed_index : entity["offset"]]
            new_processed_index = entity["offset"] + entity["length"]
            command = original_text[entity["offset"] : new_processed_index]
            processed_index = new_processed_index

            if command.endswith(f"@{self.username}"):
                text += command[: -len(f"@{self.username}")]
            else:
                text += command

        return text + original_text[processed_index:]

    def _make_update(self, raw_update):
        if "message" not in raw_update:
            return raw_update

        attachments = []

        for kind in TELEGRAM_POSSIBLE_ATTACHMENT_KINDS:
            if raw_update["message"].get(kind):
                attachments.append(
                    self._make_attachment(raw_update["message"][kind], kind)
                )

        if raw_update["message"]["chat"]["type"] == "private":
            recipient_kind = RecipientKind.PRIVATE_CHAT
        else:
            recipient_kind = RecipientKind.GROUP_CHAT

        return Message(
            sender_id=raw_update["message"]["from"]["id"],
            recipient_id=raw_update["message"]["chat"]["id"],
            recipient_kind=recipient_kind,
            text=self._extract_text(raw_update) or "",
            attachments=attachments,
            date=raw_update["message"]["date"],
            raw=raw_update,
        )

    async def acquire_updates(self, queue: asyncio.Queue):
        offset = 0

        while True:
            try:
                response = await self.request(
                    "getUpdates", {"timeout": 25, "offset": offset}
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Exceptions while gettings updates (Telegram)")
                await asyncio.sleep(1)
                continue

            for raw_update in response:
                await queue.put((self._make_update(raw_update), self))
                offset = raw_update["update_id"] + 1

    async def send_message(self, recipient_id, text, attachments, **kwargs):
        results = []

        async with self.api_messages_lock:
            if text:
                results.append(
                    await self.request(
                        "sendMessage",
                        {
                            "chat_id": recipient_id,
                            "text": str(text),
                            **kwargs,
                        },
                    )
                )
                await asyncio.sleep(self.api_messages_pause)

            for attachment in attachments or ():
                if not isinstance(attachment, Attachment):
                    raise ValueError(f'Unexpected attachment: "{attachment}"')

                if attachment.kind not in SUPPORTED_ATTACHMENT_KINDS:
                    raise ValueError(
                        f'Unsupported attachment kind: "{attachment.kind}"'
                    )

                method, data_field = SUPPORTED_ATTACHMENT_KINDS[attachment.kind]

                results.append(
                    await self.request(
                        method,
                        pick_by(
                            {
                                "chat_id": recipient_id,
                                data_field: attachment.id or attachment.content or None,
                                "caption": attachment.title
                                or (
                                    attachment.content[0]
                                    if attachment.content
                                    else None
                                ),
                            }
                        ),
                    )
                )

                await asyncio.sleep(self.api_messages_pause)

        return results

    async def on_shutdown(self, app):
        await self.client.aclose()
