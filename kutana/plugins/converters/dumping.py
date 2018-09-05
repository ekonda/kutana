from kutana.plugins.data import Message


async def convert_to_message(arguments, update, env, extenv):
    arguments["message"] = Message(
        update,
        (),
        "PC",
        "KUTANA",
        update
    )

    arguments["attachments"] = arguments["message"].attachments

    env["reply"] = print
