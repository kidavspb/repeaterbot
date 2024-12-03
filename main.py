import time

from code_modules.actions.delete import delete_propagation
from code_modules.actions.edit import edit_propagation
from code_modules.actions.send import make_propagation, too_late
from code_modules.utils.commands import *

while True:
    try:
        @bot.message_handler(commands=['start'], chat_types=['private'])
        def welcome_menu(message):
            if message.from_user.id in white_list_manager.get_data():
                bot.send_message(message.from_user.id, "Что вы хотите сделать?", reply_markup=create_menu_markup())
                logging.info(f"Start message from user in white list @{message.from_user.username}")
            else:
                logging.info(f"Start message from user not in white list @{message.from_user.username}")


        def create_menu_markup():
            markup = telebot.types.InlineKeyboardMarkup()

            btn1 = telebot.types.InlineKeyboardButton("📢 Отправить новое сообщение", callback_data=ActionType.SEND.value)
            btn2 = telebot.types.InlineKeyboardButton("✏️ Изменить предыдущее сообщение", callback_data=ActionType.EDIT.value)
            btn3 = telebot.types.InlineKeyboardButton("🪓 Удалить предыдущее сообщение", callback_data=ActionType.DELETE.value)

            markup.add(btn1)
            markup.add(btn2)
            markup.add(btn3)

            return markup


        @bot.message_handler(content_types=['new_chat_members'],
                             func=lambda message: message.chat.id not in chats_manager.get_data())
        def added_to_new_chat(message):
            for member in message.new_chat_members:
                if member.id == BOT_ID:
                    initiator = message.from_user
                    place = message.chat
                    bot.send_message(ADMIN_ID, f"@{initiator.username} ({initiator.full_name}) добавил бота в чат: \"{place.title}\"({place.id})" + "\n\n" +
                                     f"Чтобы добавить чат в список, введите команду: <code>/add_chat {place.id} {place.title}</code>",
                                     parse_mode="HTML")
                    logging.info(f"@{initiator.username} ({initiator.id}) added bot to chat: \"{place.title}\"({place.id})")


        @bot.callback_query_handler(func=lambda call: True)
        def callback(call):
            if call.data == "cancel":
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Отправка сообщения отменена 👌")
                logging.info(f"Cancel message from user @{call.message.chat.username}")
            elif call.data == "send_now" or (call.data == ActionType.SEND.value and not too_late(call.message)):
                logging.info(f"'Send' option selected by user @{call.message.chat.username}")
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Напишите сообщение, которое будет отправлено во все чаты")
                bot.register_next_step_handler(call.message, make_propagation)
            elif call.data == ActionType.EDIT.value:
                logging.info(f"'Edit' option selected by user @{call.message.chat.username}")
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Напишите идентификатор рассылки, текст в которой хотите изменить")
                bot.register_next_step_handler(call.message, edit_propagation)
            elif call.data == ActionType.DELETE.value:
                logging.info(f"'Delete' option selected by user @{call.message.chat.username}")
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Напишите идентификатор рассылки, которую хотите удалить")
                bot.register_next_step_handler(call.message, delete_propagation)


        logging.info("Bot running..")
        bot.polling(none_stop=True)

    except Exception as e:
        logging.error(e)
        bot.stop_polling()

        time.sleep(15)

        logging.info("Running again!")
