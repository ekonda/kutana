from kutana import Plugin
import random

plugin = Plugin(name="(.кто | .кого | .кому) - выбор пользователя из конференции")

template = ["Нуу я думаю", "Скорее всего", "Звезды говорят", "Мама сказала", "Без сомнений", "Ну это же очевидно", "Только тсс"]

@plugin.on_startswith_text("кто", "кого", "кому")
async def report(mes, at, env):
    if mes.peer_id == mes.from_id:
        return await env.reply("Команда доступна только в беседах")

    if not env.body:
        return await env.reply("Используйте: (.кто | .кого | .кому) [текст]")

    users = await env.request("messages.getConversationMembers", peer_id=mes.peer_id, fields='name')
    if users.error:
        return await env.reply("Произошла ошибка при получении участников конференции. Скорее всего вы не выдали боту права администратора беседы")
   
    users = users.response

    user = random.choice(users["profiles"])

    return await env.reply(f"{random.choice(template)}, @id{user['id']} ({user['first_name']} {user['last_name']})")
