from kutana.plugins.data import Message, Attachment


async def prepare(arguments, update, env, extenv):
    arguments["message"] = Message(
        update,
        (),
        "PC",
        "KUTANA",
        update
    )

    arguments["attachments"] = arguments["message"].attachments

    env["reply"] = print
