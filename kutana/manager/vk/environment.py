import json
import re
import aiohttp
from kutana.plugin import Message, Attachment
from kutana.environment import Environment


NAIVE_CACHE = {}


class VKEnvironment(Environment):
    def spawn(self):
        return self.__class__(self.manager, self, peer_id=self.peer_id)

    async def upload_file_to_vk(self, upload_url, data):
        upload_result_resp = await self.manager.session.post(
            upload_url, data=data
        )

        if not upload_result_resp:
            return None

        upload_result_text = await upload_result_resp.text()

        if not upload_result_text:
            return None

        try:
            upload_result = json.loads(upload_result_text)

            if "error" in upload_result:
                raise RuntimeError

        except RuntimeError:
            return None

        return upload_result

    async def request(self, method, **kwargs):
        """Proxy for manager's `request` method."""

        return await self.manager.request(method, **kwargs)

    async def send_message(self, message, peer_id, attachment=None,
                           sticker_id=None, payload=None, keyboard=None,
                           forward_messages=None):
        """Proxy for manager's `send_message` method."""

        return await self.manager.send_message(
            message,
            peer_id,
            attachment,
            sticker_id,
            payload,
            keyboard,
            forward_messages
        )

    async def reply(self, message, attachment=None, sticker_id=None,
                    payload=None, keyboard=None, forward_messages=None):

        if self.peer_id is None:
            return ()

        if len(message) < 4096:
            return (await self.manager.send_message(
                message,
                self.peer_id,
                attachment,
                sticker_id,
                payload,
                keyboard,
                forward_messages
            ),)

        result = []

        chunks = list(
            message[i : i + 4096] for i in range(0, len(message), 4096)
        )

        for chunk in chunks[:-1]:
            result.append(
                await self.manager.send_message(chunk, self.peer_id)
            )

        result.append(
            await self.manager.send_message(
                chunks[-1],
                self.peer_id,
                attachment,
                sticker_id,
                payload,
                keyboard,
                forward_messages
            )
        )

        return result

    async def upload_doc(self, file, peer_id=None, group_id=None,
                         doctype="doc", filename=None):
        """Pass peer_id=False to upload with docs.getWallUploadServer."""

        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        if peer_id:
            upload_data = await self.manager.request(
                "docs.getMessagesUploadServer", peer_id=peer_id, type=doctype
            )

        else:
            upload_data = await self.manager.request(
                "docs.getWallUploadServer",
                group_id=group_id or self.manager.group_id
            )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)

        upload_result = await self.upload_file_to_vk(upload_url, data)

        if not upload_result:
            return None

        attachments = await self.manager.request(
            "docs.save", **upload_result
        )

        if not attachments.response:
            return None

        return self.convert_to_attachment(
            attachments.response[0], "doc"
        )

    async def upload_photo(self, file, peer_id=None):
        """
        Upload passed file to vk.com. If `peer_id` was passed, file will be
        uploaded for user with `peer_id`.

        :param file: file to be uploaded. Can be bytes, file-like object or
            path to file as string
        :param peer_id: user's id to file to be uploaded for
        :rtype: :class:`Attachment`
        """

        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as fh:
                file = fh.read()

        upload_data = await self.manager.request(
            "photos.getMessagesUploadServer", peer_id=peer_id
        )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("photo", file, filename="image.png")

        upload_result = await self.upload_file_to_vk(upload_url, data)

        if not upload_result:
            return None

        attachments = await self.manager.request(
            "photos.saveMessagesPhoto", **upload_result
        )

        if not attachments.response:
            return None

        return self.convert_to_attachment(
            attachments.response[0], "photo"
        )

    async def resolve_screen_name(self, screen_name):
        """Return answer from vk.com with resolved passed screen name."""

        if screen_name in NAIVE_CACHE:
            return NAIVE_CACHE[screen_name]

        result = await self.manager.request(
            "utils.resolveScreenName",
            screen_name=screen_name
        )

        NAIVE_CACHE[screen_name] = result

        return result

    async def convert_to_message(self, update):
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
            tuple(self.convert_to_attachment(a) for a in obj["attachments"]),
            obj.get("from_id"),
            obj.get("peer_id"),
            update
        )

    @staticmethod
    def convert_to_attachment(attachment, attachment_type=None):
        """
        Create and return :class:`.Attachment` created from passed data. If
        attachmnet type can't be determined passed `attachment_type`
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
                if size["width"] > m_s_wid:
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
