from kutana.controllers.vk.converter import convert_to_attachment
import aiohttp
import json


async def upload_file_to_vk(ctrl, upload_url, data):
    upload_result_resp = await ctrl.session.post(
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
            raise Exception

    except Exception:
        return None

    return upload_result


class reply_concrete_class():
    """Class-method for replying to messages."""

    def __init__(self, ctrl, peer_id):
        self.ctrl = ctrl
        self.peer_id = peer_id

    async def __call__(self, message, attachment=None, sticker_id=None, payload=None, keyboard=None):
        return await self.ctrl.send_message(
            message,
            self.peer_id,
            attachment,
            sticker_id,
            payload,
            keyboard
        )


class upload_doc_class():
    """Class-method for uploading documents.
    """

    def __init__(self, ctrl, peer_id):
        self.ctrl = ctrl
        self.peer_id = peer_id

    async def __call__(self, file, peer_id=None, group_id=None,
            doctype="doc", filename=None):
        """Pass peer_id=False to upload with docs.getWallUploadServer."""

        if filename is None:
            filename = "file.png"

        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        if peer_id:
            upload_data = await self.ctrl.request(
                "docs.getMessagesUploadServer", peer_id=peer_id, type=doctype
            )

        else:
            upload_data = await self.ctrl.request(
                "docs.getWallUploadServer",
                group_id=group_id or self.ctrl.group_id
            )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)

        upload_result = await upload_file_to_vk(self.ctrl, upload_url, data)

        if not upload_result:
            return None

        attachments = await self.ctrl.request(
            "docs.save", **upload_result
        )

        if not attachments.response:
            return None

        return convert_to_attachment(
            attachments.response[0], "doc"
        )


class upload_photo_class():
    """Class-method for uploading documents."""

    def __init__(self, ctrl, peer_id):
        self.ctrl = ctrl
        self.peer_id = peer_id

    async def __call__(self, file, peer_id=None):
        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        upload_data = await self.ctrl.request(
            "photos.getMessagesUploadServer", peer_id=peer_id
        )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("photo", file, filename="image.png")

        upload_result = await upload_file_to_vk(self.ctrl, upload_url, data)

        if not upload_result:
            return None

        attachments = await self.ctrl.request(
            "photos.saveMessagesPhoto", **upload_result
        )

        if not attachments.response:
            return None

        return convert_to_attachment(
            attachments.response[0], "photo"
        )
