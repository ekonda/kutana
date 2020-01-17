import asyncio
import aiohttp
import json
from ..backend import Backend
from ..update import Message, ReceiverType, Update, UpdateType, Attachment
from ..exceptions import RequestException
from ..logger import logger


class Telegram(Backend):
    def __init__(
        self,
        token,
        messages_per_second=29,
        session=None,
        proxy=None,
        api_url="https://api.telegram.org"
    ):
        if not token:
            raise ValueError("No `token` specified")

        self.offset = 0

        self.proxy = proxy
        self.session = session
        self._is_session_local = session is None

        self.api_token = token
        self.api_messages_pause = 1 / messages_per_second
        self.api_messages_lock = None

        self.api_url = f"https://api.telegram.org/bot{token}/{{}}"
        self.file_url = f"https://api.telegram.org/file/bot{token}/{{}}"

    async def _request(self, method, kwargs={}):
        if not self.session:
            self.session = aiohttp.ClientSession()

        data = {k: v for k, v in kwargs.items() if v is not None}

        url = self.api_url.format(method)

        async with self.session.post(url, proxy=self.proxy, data=data) as resp:
            data = await resp.json(content_type=None)

            if not data.get("ok"):
                raise RequestException(self, (method, {**kwargs}), data)

        res = data["result"]

        logger.debug("Telegram: %s(%s) => %s", method, kwargs, res)

        return res

    async def _request_file(self, file_id):
        file = await self._request("getFile", {"file_id": file_id})

        url = self.file_url.format(file["file_path"])

        async with self.session.get(url, proxy=self.proxy) as resp:
            return await resp.read()

    def _make_getter(self, file_id):
        async def getter():
            return await self._request_file(file_id)
        return getter

    def _make_attachment(self, raw_attachment, raw_attachment_type):
        t = raw_attachment_type
        d = raw_attachment

        if "file_id" in d:
            id = d["file_id"]
        else:
            id = None

        if t == "photo":
            photo = list(sorted(d, key=lambda p: p["width"]))[-1]
            id = photo["file_id"]
            return Attachment._existing_full(
                id=id, type="image", title="", file_name=id,
                getter=self._make_getter(id), raw=d,
            )

        elif t == "audio":
            title = d.get("performer", "") + " - " + d.get("title", "")
            return Attachment._existing_full(
                id=id, type="audio", title=title,
                file_name=id, getter=self._make_getter(id), raw=d,
            )

        elif t == "document":
            return Attachment._existing_full(
                id=id, type="doc", title="",
                file_name=d.get("file_name", ""),
                getter=self._make_getter(id), raw=d,
            )

        elif t == "sticker":
            return Attachment._existing_full(
                id=id, type="sticker", title="", file_name=id,
                getter=self._make_getter(id), raw=d,
            )

        elif t == "voice":
            return Attachment._existing_full(
                id=id, type="voice", title="", file_name=id,
                getter=self._make_getter(id), raw=d,
            )

        elif t == "video":
            return Attachment._existing_full(
                id=id, type="video", title="", file_name=id,
                getter=self._make_getter(id), raw=d,
            )

        else:
            return Attachment._existing_full(
                id=None, type=t, title=None, file_name=None, getter=None,
                raw=d,
            )

    def _make_update(self, raw_update):
        if "message" not in raw_update:
            return Update(raw_update, UpdateType.UPD)

        attachments = []

        possible_types = (
            "audio", "voice", "photo", "video", "document", "sticker",
            "animation", "video_note", "contact", "location", "venue",
            "poll", "invoice"
        )

        for key in possible_types:
            if key in raw_update["message"]:
                attachments.append(
                    self._make_attachment(raw_update["message"][key], key)
                )

        if raw_update["message"]["chat"]["type"] == "private":
            receiver_type = ReceiverType.SOLO
        else:
            receiver_type = ReceiverType.MULTI

        return Message(
            raw=raw_update,
            type=UpdateType.MSG,
            text=raw_update["message"].get("text", ""),
            attachments=attachments,
            sender_id=raw_update["message"]["from"]["id"],
            receiver_id=raw_update["message"]["chat"]["id"],
            receiver_type=receiver_type,
            date=raw_update["message"]["date"],
        )

    async def perform_updates_request(self, submit_update):
        try:
            response = await self._request(
                "getUpdates", {"timeout": 25, "offset": self.offset}
            )
        except (json.JSONDecodeError, aiohttp.ClientError):
            return

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Exceptions while gettings updates (Telegram)")
            await asyncio.sleep(1)
            return

        for update in response:
            await submit_update(self._make_update(update))
            self.offset = update["update_id"] + 1

    async def perform_send(self, target_id, message, attachments, kwargs):
        result = []

        chat_id = str(target_id)

        async with self.api_messages_lock:
            if message:
                result.append(await self._request("sendMessage", {
                    "chat_id": chat_id,
                    "text": message,
                    **kwargs,
                }))

                await asyncio.sleep(self.api_messages_pause)

            if isinstance(attachments, (int, str, Attachment)):
                attachments = (attachments,)

            new_attachments = []

            for a in attachments:
                if isinstance(a, Attachment):
                    attach_type = {
                        "doc": "document",
                        "image": "photo",
                    }.get(a.type, a.type)

                    if a.uploaded:
                        new_attachments.append((attach_type, str(a.id)))
                    else:
                        new_attachments.append((attach_type, a.file))

            for atype, acontent in new_attachments:
                if atype not in (
                    "document", "photo", "audio", "video", "voice", "sticker"
                ):
                    raise ValueError(f"Can't upload attachment '{atype}'")

                result.append(
                    await self._request(
                        "send" + atype.capitalize(),
                        {"chat_id": chat_id, atype: acontent}
                    )
                )

                await asyncio.sleep(self.api_messages_pause)

            return result

    async def perform_api_call(self, method, kwargs):
        return await self._request(method, kwargs)

    async def on_start(self, app):
        me = await self._request("getMe")

        name = me["first_name"]
        if me.get("last_name"):
            name += " " + me["last_name"]

        logger.info(
            'logged in as "%s" ( https://t.me/%s )',
            name,
            me["username"],
        )

        self.api_messages_lock = asyncio.Lock(loop=app.get_loop())

    async def send_message(self, target_id, message, attachments=(), **kwargs):
        """
        Send message to specified `target_id` with text `message` and
        attachments `attachments`.

        This method will forward all excessive keyword arguments to
        sending method.
        """

        return await self.perform_send(target_id, message, attachments, kwargs)

    async def request(self, method, **kwargs):
        """
        Call specified method from Telegram api with specified
        kwargs and return response's data.
        """

        return await self._request(method, kwargs)

    async def on_shutdown(self, app):
        if self._is_session_local:
            await self.session.close()
