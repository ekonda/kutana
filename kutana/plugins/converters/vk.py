from kutana.plugins.data import Message, Attachment
import re

def convert_to_attachment(attachment, attachment_type=None):
    if "type" in attachment and attachment["type"] in attachment:
        body = attachment[attachment["type"]]
        attachment_type = attachment["type"]
    else:
        body = attachment

    if "sizes" in body:
        link = body["sizes"][-1]["url"]  # src

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


naive_cache = {}

async def resolveScreenName(screen_name, extenv):  # pragma: no cover
    if screen_name in naive_cache:
        return naive_cache[screen_name]

    result = await extenv.request(
        "utils.resolveScreenName",
        screen_name=screen_name
    )

    naive_cache[screen_name] = result

    return result


async def convert_to_message(arguments, update, env, extenv):
    if update["type"] != "message_new":
        return True

    obj = update["object"]

    text = obj["text"]

    if "conversation_message_id" in obj:
        cursor = 0
        new_text = ""

        for m in re.finditer(r"\[(.+?)\|.+?\]", text):
            resp = await resolveScreenName(m.group(1), extenv)

            new_text += text[cursor : m.start()]

            cursor = m.end()

            if resp.error or resp.response["object_id"] == update["group_id"]:
                continue

            new_text += text[m.start() : m.end()]

        new_text += text[cursor :]

        text = new_text.lstrip()

    arguments["message"] = Message(
        text,
        tuple(convert_to_attachment(a) for a in obj["attachments"]),
        obj.get("from_id"),
        obj.get("peer_id"),
        update
    )

    arguments["attachments"] = arguments["message"].attachments

    for w in ("reply", "send_msg", "request", "upload_photo", "upload_doc"):
        env[w] = extenv[w]
