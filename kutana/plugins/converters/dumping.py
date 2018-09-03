from kutana.plugins.data import Message


async def convert_to_message(update, env):
    return Message(
        update, (), "U", "KU", update
    )
