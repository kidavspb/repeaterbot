from datetime import datetime
from code_modules.utils.init import *
from code_modules.main_pipeline import make_action


def make_propagation(message):
    make_action(ActionType.SEND, message, hash(message))


def too_late(message):
    if quiet_time["start"] <= datetime.now().hour or datetime.now().hour < quiet_time["end"]:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id,
                         "Сейчас ночь, все спят. Вы уверены, что хотите отправить сообщение прямо сейчас?",
                         reply_markup=create_confirmation_markup())
        logging.info(f"Too late message to user @{message.chat.username}")
        return True
    else:
        return False


def create_confirmation_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ Да", callback_data="send_now"),
               telebot.types.InlineKeyboardButton("❌ Нет, отмена", callback_data="cancel"))
    return markup