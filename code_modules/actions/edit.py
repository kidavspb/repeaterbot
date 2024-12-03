from code_modules.utils.init import *
from code_modules.main_pipeline import make_action


def edit_propagation(message):
    if message.text == "/cancel":
        logging.info(f"Cancel message from user @{message.from_user.username}")
        bot.send_message(message.chat.id, "Отменено")
        return
    try:
        message_hash = int(message.text)
        if message_hash not in messages_manager.get_data(): raise KeyError
        logging.info(f"User @{message.from_user.username} send message hash {message_hash} to edit")
        bot.send_message(message.chat.id, "Напишите новый текст сообщения")
        bot.register_next_step_handler(message,
                                       lambda new_message: make_action(ActionType.EDIT, new_message, message_hash))
    except KeyError:
        bot.send_message(message.chat.id, "Рассылки с таким идентификатором не существует", reply_to_message_id=message.message_id)
        logging.error(f"Message with such hash not found by @{message.from_user.username}")
    except Exception as e:
        bot.send_message(message.chat.id, "Не похоже на идентификатор рассылки", reply_to_message_id=message.message_id)
        logging.error(f"Something wrong when @{message.from_user.username} tried to edit message")
        logging.error(e)
