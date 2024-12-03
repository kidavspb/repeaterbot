from code_modules.utils.init import *
from code_modules.utils.other import beautiful_action, beautiful_numeral, forward_or_copy


def repeater(action_type: ActionType, message, message_hash):  # непосредственно действие (отправка, редактирование, удаление) во всех чатах
    not_successful_chats = []

    chat_ids = []
    msg_ids = []

    match action_type:
        case ActionType.SEND:
            for chat_id in chats_manager.get_data():
                try:
                    msg_id = forward_or_copy(chat_id, message).message_id
                    chat_ids.append(chat_id)
                    msg_ids.append(msg_id)
                except Exception as e:
                    not_successful_chats.append(chat_id)
                    logging.error(f"Something wrong with chat {chat_id} when {action_type.value} message")
                    logging.error(e)
            messages_manager.add_data(message_hash, {"chat_ids": chat_ids, "msg_ids": msg_ids})
        case ActionType.EDIT:
            data = messages_manager.get_data()[message_hash]
            for chat_id, msg_id in zip(data["chat_ids"], data["msg_ids"]):
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                          text=message.text, entities=message.entities)
                    chat_ids.append(chat_id)
                except Exception as e:
                    not_successful_chats.append(chat_id)
                    logging.error(f"Something wrong with chat {chat_id} when {action_type.value} message")
                    logging.error(e)
        case ActionType.DELETE:
            data = messages_manager.get_data()[message_hash]
            for chat_id, msg_id in zip(data["chat_ids"], data["msg_ids"]):
                try:
                    bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    chat_ids.append(chat_id)
                except Exception as e:
                    not_successful_chats.append(chat_id)
                    logging.error(f"Something wrong with chat {chat_id} when {action_type.value} message")
                    logging.error(e)
            messages_manager.del_data(message_hash)

    return chat_ids, not_successful_chats


def tell_result(successful_chats, not_successful_chats, action_type: ActionType, message_id, message_hash, user):  # сообщение инициатору действия о его результате
    result_text = beautiful_action(action_type, len(successful_chats), len(not_successful_chats))
    logging_text = f"Message {action_type.value} in {len(successful_chats)} chats by @{user.username}"

    if not_successful_chats and successful_chats:
        result_text += ", ".join(chats_manager.get_data()[chat_id] for chat_id in not_successful_chats)
        logging_text = f"Message {action_type.value} in {len(successful_chats)} chats except {len(not_successful_chats)}: id{not_successful_chats} by @{user.username}"

    if action_type is ActionType.SEND: result_text += f"\n\nИдентификатор этой рассылки: <code>{message_hash}</code>"
    bot.send_message(user.id, result_text, reply_to_message_id=message_id, parse_mode="HTML")
    logging.info(logging_text)


def notify(action_type: ActionType, message, successful_count):  # сообщение всем остальным членам белого списка о рассылке  # TODO: сделать не только для send
    if action_type is ActionType.SEND:
        if successful_count == 0:
            info_part = f"👆 Это сообщение хотел отправить, но не смог @{message.from_user.username} ({message.from_user.full_name})"
        else:
            info_part = f"👆 Это сообщение в {beautiful_numeral(action_type, successful_count)} отправил @{message.from_user.username} ({message.from_user.full_name})"
        info_part += f"\n\nИдентификатор этой рассылки: <code>{hash(message)}</code>"
        for user_id in white_list_manager.get_data():
            try:
                if user_id == message.from_user.id: continue
                else:
                    msg = bot.send_message(user_id, message.text, entities=message.entities)
                    bot.send_message(user_id, info_part, reply_to_message_id=msg.id, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Something wrong with member {user_id}")
                logging.error(e)


def make_action(action_type: ActionType, message, message_hash):  # TODO: не давать отправлять команды
    if message.text == "/cancel":
        logging.info(f"Cancel message from user @{message.from_user.username}")
        bot.send_message(message.chat.id, "Отменено")
        return
    successful_chats, not_successful_chats = repeater(action_type, message, message_hash)
    tell_result(successful_chats, not_successful_chats, action_type, message.id, message_hash, message.from_user)
    notify(action_type, message, len(successful_chats))