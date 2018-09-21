from kutana.controller_vk.converter import convert_to_attachment
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


def make_reply(ctrl, peer_id):
    """Creates replying coroutine for controller and peer_id."""

    async def reply(message, attachment=None, sticker_id=None,
            payload=None, keyboard=None):

        if len(message) > 4096:
            result = []

            for i in range(0, len(message), 4096):
                result.append(
                    await ctrl.send_message(
                        message[i : i + 4096],
                        peer_id,
                        attachment,
                        sticker_id,
                        payload,
                        keyboard
                    )
                )

            return result

        return [await ctrl.send_message(
            message,
            peer_id,
            attachment,
            sticker_id,
            payload,
            keyboard
        )]

    return reply


def make_upload_docs(ctrl, ori_peer_id):
    """Creates uploading docs coroutine for controller and peer_id."""

    async def upload_doc(file, peer_id=None, group_id=None,
            doctype="doc", filename=None):
        """Pass peer_id=False to upload with docs.getWallUploadServer."""

        if filename is None:
            filename = "file.png"

        if peer_id is None:
            peer_id = ori_peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        if peer_id:
            upload_data = await ctrl.request(
                "docs.getMessagesUploadServer", peer_id=peer_id, type=doctype
            )

        else:
            upload_data = await ctrl.request(
                "docs.getWallUploadServer",
                group_id=group_id or ctrl.group_id
            )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)

        upload_result = await upload_file_to_vk(ctrl, upload_url, data)

        if not upload_result:
            return None

        attachments = await ctrl.request(
            "docs.save", **upload_result
        )

        if not attachments.response:
            return None

        return convert_to_attachment(
            attachments.response[0], "doc"
        )

    return upload_doc


def make_upload_photo(ctrl, ori_peer_id):
    """Creates uploading photo coroutine for controller and peer_id"""

    async def upload_photo(file, peer_id=None):
        if peer_id is None:
            peer_id = ori_peer_id

        if isinstance(file, str):
            with open(file, "rb") as o:
                file = o.read()

        upload_data = await ctrl.request(
            "photos.getMessagesUploadServer", peer_id=peer_id
        )

        if "upload_url" not in upload_data.response:
            return None

        upload_url = upload_data.response["upload_url"]

        data = aiohttp.FormData()
        data.add_field("photo", file, filename="image.png")

        upload_result = await upload_file_to_vk(ctrl, upload_url, data)

        if not upload_result:
            return None

        attachments = await ctrl.request(
            "photos.saveMessagesPhoto", **upload_result
        )

        if not attachments.response:
            return None

        return convert_to_attachment(
            attachments.response[0], "photo"
        )

    return upload_photo
