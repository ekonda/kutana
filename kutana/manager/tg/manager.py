"""Manager for interacting with telegram."""

import json
from collections import namedtuple

import aiohttp
from kutana.logger import logger
from kutana.manager.basic import BasicManager
from kutana.manager.tg.environment import TGEnvironment, TGAttachmentTemp
from kutana.plugin import Attachment, Message


TGResponse = namedtuple(
    "TGResponse",
    "error errors response"
)

TGResponse.__doc__ = """
"error" is a boolean value indicating if errorhappened.
"errors" contains array with happened errors.
"response" contains result of reqeust if no errors happened.
"""


class TGManager(BasicManager):
    """
    Class for receiving updates from telegram. Controller requires bot's
    token.
    """


    type = "telegram"


    def __init__(self, token, proxy=None):
        if not token:
            raise ValueError('No "token" specified')

        self.session = None

        self.offset = 0
        self.proxy = proxy

        self.token = token

        self.api_url = \
            "https://api.telegram.org/bot{}/{{}}".format(self.token)
        self.file_url = \
            "https://api.telegram.org/file/bot{}/{{}}".format(self.token)

    async def get_environment(self, update):
        if "message" in update:
            peer_id = update["message"]["chat"]["id"]

        else:
            peer_id = None

        return TGEnvironment(self, peer_id=peer_id)

    async def get_background_coroutines(self, ensure_future):
        return ()

    async def request_file(self, path):
        """
        Download file with specified path and return it as bytes.

        :param path: Telegram's file's path for downloading
        :rtype: bytes or None
        """

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                    self.file_url.format(path), proxy=self.proxy
                ) as response:

                return await response.read()

        except aiohttp.ClientError:
            return None

    async def request(self, method, **kwargs):
        """
        Perform request to telegram and return result.

        :param method: method to call
        :param kwargs: parameters for method
        :rtype: :class:`.TGResponse`
        """

        if not self.session:
            self.session = aiohttp.ClientSession()

        data = {k: v for k, v in kwargs.items() if v is not None}

        try:
            async with self.session.post(
                    self.api_url.format(method), proxy=self.proxy, data=data
                ) as response:

                raw_respose_text = await response.text()

                raw_respose = json.loads(raw_respose_text)

        except (json.JSONDecodeError, aiohttp.ClientError) as e:
            return TGResponse(
                error=True,
                errors=(("Kutana", str(type(e)) + ": " + str(e)),),
                response=""
            )

        if not raw_respose["ok"]:
            return TGResponse(
                error=True,
                errors=(
                    ("TG_err", (
                        raw_respose.get("error_code", ""),
                        raw_respose.get("description", "")
                    ))
                ),
                response=""
            )

        return TGResponse(
            error=False,
            errors=(),
            response=raw_respose["result"]
        )

    async def send_message(self, message, peer_id, attachment=None, **kwargs):
        """
        Send message to target peer_id with parameters.

        :param message: text to send
        :param peer_id: target recipient
        :param attachment: list of instances of :class:`.Attachment` or
            :class:`.TGAttachmentTemp`
        :parma kwargs: arguments to send to telegram's `sendMessage`
        :rtype: list of responses from telegram
        """

        if peer_id is None:
            return ()

        peer_id_str = str(peer_id)

        result = []

        if message:
            message_parts = self.split_large_text(message)

            for part in message_parts:
                result.append(
                    await self.request(
                        "sendMessage", chat_id=peer_id_str, text=part, **kwargs
                    )
                )

        if isinstance(attachment, (Attachment, TGAttachmentTemp)):
            attachment = [attachment]

        if isinstance(attachment, (list, tuple)):
            new_attachment = []

            for a in attachment:
                if isinstance(a, Attachment):
                    attachment_type = "document" if a.type == "doc" else a.type

                    new_attachment.append((attachment_type, str(a.id), {}))

                elif isinstance(a, TGAttachmentTemp):
                    new_attachment.append((a.type, a.content, a.kwargs))

            attachment = new_attachment

        if attachment:
            for attachment_type, content, upload_kwargs in attachment:
                if attachment_type not in ("document", "photo", "audio",
                                           "video", "voice"):
                    continue

                result.append(
                    await self.request(
                        "send" + attachment_type.capitalize(),
                        **{
                            "chat_id": peer_id_str,
                            attachment_type: content,
                            **upload_kwargs
                        }
                    )
                )

        return result

    async def create_message(self, update):
        if "message" not in update:
            return None

        attachments = []

        for key in ("audio", "photo", "video", "document"):
            attachments.append(
                self.create_attachment(update["message"].get(key), key)
            )

        return Message(
            update["message"].get("text", ""),
            tuple(a for a in attachments if a),
            update["message"]["from"]["id"],
            update["message"]["chat"]["id"],  # peer_id
            update["message"]["date"],
            update
        )

    @staticmethod
    def create_attachment(attachment, attachment_type=None):
        """
        Create and return :class:`.Attachment` created from passed data. If
        attachment type can't be determined passed "attachment_type"
        well be used.
        """

        if not attachment:
            return None

        if attachment_type == "document":
            attachment_type = "doc"

        elif attachment_type == "photo":
            attachment = attachment[-1]

        return Attachment(
            attachment_type,
            attachment.get("file_id"),
            None,
            None,
            None,
            attachment
        )

    async def receiver(self):
        """Return new updates for bot from vkontakte."""

        response = await self.request(
            "getUpdates", timeout=25, offset=self.offset
        )

        if response.error or not response.response:
            return ()

        updates = response.response

        self.offset = updates[-1]["update_id"] + 1

        return updates

    async def get_receiver_coroutine_function(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

        response = await self.request("getMe")

        if response.error:
            raise ValueError("Wrong token for TGManager")

        logger.info(
            "logged in as \"%s\" ( https://t.me/%s )",
            (
                response.response.get("first_name", "") + " " +
                response.response.get("last_name", "")
            ).strip(),
            response.response["username"]
        )

        return self.receiver

    async def dispose(self):
        if self.session:
            await self.session.close()
