from code_modules.utils.init import *


@bot.message_handler(commands=['help'], func=lambda message: message.from_user.id == ADMIN_ID)
def help(message):
    text = "*Список команд:*\n\n" \
           "/start — начать рассылку\n" \
           "/help — помощь\n\n" \
           "`/add\_chat id title` — добавить чат в список\n" \
           "`/delete\_chat id` — удалить чат из списка\n" \
           "`/add\_member id username` — добавить пользователя в белый список\n" \
           "`/delete\_member id` — удалить пользователя из белого списка\n\n" \
           "/show\_chats — показать список чатов\n" \
           "/show\_members — показать список пользователей\n"
    bot.send_message(message.from_user.id, text, parse_mode="MarkdownV2")
    logging.info(f"Sent help message to user @{message.from_user.username}")


@bot.message_handler(commands=['add_chat'], func=lambda message: message.from_user.id == ADMIN_ID)
def add_chat(message):
    splitted_text = message.text.split(maxsplit=2)
    if len(splitted_text) == 3:
        new_id = int(splitted_text[1])
        new_title = splitted_text[2]
        chats_manager.add_data(new_id, new_title)
        logging.info(f"Chat {new_id}:\"{new_title}\" added to CHATS_LIST by @{message.from_user.username}")
        bot.send_message(message.from_user.id, f"Чат {new_id}:\"{new_title}\" добавлен в список")
    else:
        bot.send_message(message.from_user.id, "Неверный формат команды: `/add\_chat id title`",
                         parse_mode="MarkdownV2")


@bot.message_handler(commands=['add_member'], func=lambda message: message.from_user.id == ADMIN_ID)
def add_member(message):
    splitted_text = message.text.split(maxsplit=2)
    if len(splitted_text) == 3:
        new_id = int(splitted_text[1])
        new_username = splitted_text[2]
        white_list_manager.add_data(new_id, new_username)
        logging.info(f"Member {new_id}:\"{new_username}\" added to WHITE_LIST by @{message.from_user.username}")
        bot.send_message(message.from_user.id, f"Пользователь {new_id}:\"{new_username}\" добавлен в белый список")
    else:
        bot.send_message(message.from_user.id, "Неверный формат команды: `/add\_member id username`",
                         parse_mode="MarkdownV2")


@bot.message_handler(commands=['delete_chat'], func=lambda message: message.from_user.id == ADMIN_ID)
def delete_chat(message):
    splitted_text = message.text.split(maxsplit=2)
    if len(splitted_text) == 2:
        old_id = int(splitted_text[1])
        old_title = chats_manager.get_data()[old_id]
        chats_manager.del_data(old_id)
        logging.info(f"Chat {old_id}:\"{old_title}\" deleted from CHATS_LIST by @{message.from_user.username}")
        bot.send_message(message.from_user.id, f"Чат {old_id}:\"{old_title}\" удален из списка")
    else:
        bot.send_message(message.from_user.id, "Неверный формат команды: `/delete\_chat id`", parse_mode="MarkdownV2")


@bot.message_handler(commands=['delete_member'], func=lambda message: message.from_user.id == ADMIN_ID)
def delete_member(message):
    splitted_text = message.text.split(maxsplit=2)
    if len(splitted_text) == 2:
        old_id = int(splitted_text[1])
        old_username = white_list_manager.get_data()[old_id]
        white_list_manager.del_data(old_id)
        logging.info(f"Member {old_id}:\"{old_username}\" deleted from WHITE_LIST by @{message.from_user.username}")
        bot.send_message(message.from_user.id, f"Пользователь {old_id}:\"{old_username}\" удален из белого списка")
    else:
        bot.send_message(message.from_user.id, "Неверный формат команды: `/delete\_member id`", parse_mode="MarkdownV2")


@bot.message_handler(commands=['show_chats'], func=lambda message: message.from_user.id == ADMIN_ID)
def show_chats(message):
    text = "*Список чатов:*\n\n"
    for chat_id, chat_title in chats_manager.get_data().items():
        text += f"`{chat_id}`:\"{chat_title}\"\n"
    bot.send_message(message.from_user.id, text, parse_mode="Markdown")
    logging.info(f"Sent CHATS_LIST to user @{message.from_user.username}")


@bot.message_handler(commands=['show_members'], func=lambda message: message.from_user.id == ADMIN_ID)
def show_members(message):
    text = "*Список пользователей:*\n\n"
    for member_id, member_username in white_list_manager.get_data().items():
        text += f"`{member_id}`:\"{member_username}\"\n"
    bot.send_message(message.from_user.id, text, parse_mode="MarkdownV2")
    logging.info(f"Sent WHITE_LIST to user @{message.from_user.username}")
