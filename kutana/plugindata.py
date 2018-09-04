from collections import namedtuple


Message = namedtuple(
    "Message",
    "text attachments from_id peer_id raw_update"
)

Message.__doc__ = "Text message witch possible attachments."


Attachment = namedtuple(
    "Attachment",
    "type id owner_id access_key link raw_attachment"
)

Attachment.__doc__ = "Detailed information about attachment."
