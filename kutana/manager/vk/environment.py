"""Environment for :class:`.VKManager`."""

import json
import aiohttp
from kutana.environment import Environment


class VKEnvironment(Environment):
    """Environment for :class:`.VKManager`"""

    async def _upload_file_to_vk(self, upload_url, data):
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
        """Proxy for manager's "request" method."""

        return await self.manager.request(method, **kwargs)

    async def send_message(self, message, peer_id, attachment=None, **kwargs):
        """Proxy for manager's "send_message" method."""

        return await self.manager.send_message(
            message, peer_id, attachment, **kwargs
        )

    async def reply(self, message, attachment=None, **kwargs):
        """
        Reply to currently processed message.

        :param message: message to reply with
        :param attachment: optional attachment or list of attachments to
            reply with
        :param kwargs: arguments for vkontakte's "messages.send"
        :rtype: list with results of sending messages
        """

        return await self.manager.send_message(
            message, self.peer_id, attachment=attachment, **kwargs
        )

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

        upload_result = await self._upload_file_to_vk(upload_url, data)

        if not upload_result:
            return None

        attachments = await self.manager.request(
            "docs.save", **upload_result
        )

        if not attachments.response:
            return None

        return self.manager.convert_to_attachment(
            attachments.response[0], "doc"
        )

    async def upload_photo(self, file, peer_id=None):
        """
        Upload passed file to vkontakte. If `peer_id` was passed, file will be
        uploaded for user with `peer_id`.

        :param file: file to be uploaded. Can be bytes, file-like object or
            path to file as string
        :param peer_id: user's id to file to be uploaded for
        :rtype: :class:`.Attachment`
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

        upload_result = await self._upload_file_to_vk(upload_url, data)

        if not upload_result:
            return None

        attachments = await self.manager.request(
            "photos.saveMessagesPhoto", **upload_result
        )

        if not attachments.response:
            return None

        return self.manager.convert_to_attachment(
            attachments.response[0], "photo"
        )
