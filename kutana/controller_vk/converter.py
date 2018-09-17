from kutana.plugin import Message, Attachment
import re


def convert_to_attachment(attachment, attachment_type=None):
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


naive_cache = {}

async def resolveScreenName(screen_name, eenv):  # pragma: no cover
    if screen_name in naive_cache:
        return naive_cache[screen_name]

    result = await eenv.request(
        "utils.resolveScreenName",
        screen_name=screen_name
    )

    naive_cache[screen_name] = result

    return result


async def convert_to_message(update, eenv):
    if update["type"] != "message_new":
        return None

    obj = update["object"]

    text = obj["text"]

    if "conversation_message_id" in obj:
        cursor = 0
        new_text = ""

        for m in re.finditer(r"\[(.+?)\|.+?\]", text):
            resp = await resolveScreenName(m.group(1), eenv)

            new_text += text[cursor : m.start()]

            cursor = m.end()

            if not resp.response or resp.response["object_id"] == update["group_id"]:
                continue

            new_text += text[m.start() : m.end()]

        new_text += text[cursor :]

        text = new_text.lstrip()

    return Message(
        text,
        tuple(convert_to_attachment(a) for a in obj["attachments"]),
        obj.get("from_id"),
        obj.get("peer_id"),
        update
    )
