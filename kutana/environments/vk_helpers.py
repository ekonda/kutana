from kutana.plugins.converters.vk import convert_to_attachment
import aiohttp
import json


async def upload_file_to_vk(controller, upload_url, data):
    upload_result_resp = await controller.session.post(
        upload_url, data=data
    )

    if not upload_result_resp:
        return None  # pragma: no cover

    upload_result_text = await upload_result_resp.text()

    if not upload_result_text:
        return None  # pragma: no cover

    try:
        upload_result = json.loads(upload_result_text)

        if "error" in upload_result:
            raise Exception

    except Exception:
        return None  # pragma: no cover

    return upload_result


class upload_doc_class():
    """Class-method for uploading documents.

    Pass peer_id=False to upload with docs.getWallUploadServer.
    """

    def __init__(self, controller, peer_id):
        self.controller = controller
        self.peer_id = peer_id

    async def __call__(self, file, peer_id=None, group_id=None,
            doctype="doc", filename=None):
        if filename is None:
            filename = "file.png"

        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        if peer_id:
            upload_data = await self.controller.request(
                "docs.getMessagesUploadServer", peer_id=peer_id, type=doctype
            )

        else:
            upload_data = await self.controller.request(
                "docs.getWallUploadServer",
                group_id=group_id or self.controller.group_id
            )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)

        upload_result = await upload_file_to_vk(self.controller, upload_url, data)

        if not upload_result:
            return None  # pragma: no cover

        attachments = await self.controller.request(
            "docs.save", **upload_result
        )

        if not attachments.response:
            return None  # pragma: no cover

        return convert_to_attachment(
            attachments.response[0], "doc"
        )


class upload_photo_class():
    """Class-method for uploading documents."""

    def __init__(self, controller, peer_id):
        self.controller = controller
        self.peer_id = peer_id

    async def __call__(self, file, peer_id=None):
        if peer_id is None:
            peer_id = self.peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        upload_data = await self.controller.request(
            "photos.getMessagesUploadServer", peer_id=peer_id
        )

        if "upload_url" not in upload_data.response:
            return None  # pragma: no cover

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("photo", file, filename="image.png")

        upload_result = await upload_file_to_vk(self.controller, upload_url, data)

        if not upload_result:
            return None  # pragma: no cover

        attachments = await self.controller.request(
            "photos.saveMessagesPhoto", **upload_result
        )

        if not attachments.response:
            return None  # pragma: no cover

        return convert_to_attachment(
            attachments.response[0], "photo"
        )
