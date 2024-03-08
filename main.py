import time
from utils.init import *
from utils.commands import *
from utils.other import beautiful_numeral


while True:
    try:
        @bot.message_handler(commands=['start'])
        def welcome_menu(message):
            if message.from_user.id in white_list_manager.get_data():
                bot.send_message(message.from_user.id, "Напишите сообщение, которое будет отправлено во все чаты")
                # bot.send_message(message.from_user.id, "Что вы хотите сделать?", reply_markup=create_menu_markup())
                logging.info(f"Start message from user in white list @{message.from_user.username}")
            else:
                # bot.send_message(message.from_user.id, "Вы не можете пользоваться ботом")
                logging.info(f"Start message from user not in white list @{message.from_user.username}")


        # def create_menu_markup():
        #     markup = telebot.types.InlineKeyboardMarkup()
        #
        #     btn1 = telebot.types.InlineKeyboardButton("📢 Отправить новое сообщение", callback_data="send")
        #     # btn2 = telebot.types.InlineKeyboardButton("✏️ Изменить предыдущее сообщение", callback_data="edit")
        #     # btn3 = telebot.types.InlineKeyboardButton("🪓 Удалить предыдущее сообщение", callback_data="delete")
        #
        #     markup.add(btn1)
        #     # markup.add(btn2)
        #     # markup.add(btn3)
        #
        #     return markup


        @bot.message_handler(content_types=['new_chat_members'],
                             func=lambda message: message.chat.id not in chats_manager.get_data())
        def added_to_new_chat(message):
            for member in message.new_chat_members:
                if member.id == BOT_ID:
                    new_id = message.chat.id
                    new_title = message.chat.title
                    bot.send_message(ADMIN_ID, f"Бот был добавлен в чат: \"{new_title}\"({new_id})" + "\n\n" +
                                     f"Чтобы добавить чат в список, введите команду: <code>/add_chat {new_id} {new_title}</code>",
                                     parse_mode="HTML")


        def forward_or_copy(chat_id, message):  # TODO: пересылка сообщений с несколькими медиа
            if message.forward_from_chat:
                bot.forward_message(chat_id, message.chat.id, message.id)
            else:
                bot.copy_message(chat_id, message.chat.id, message.id)


        def repeater(message):  # непосредственно отправка сообщения во все чаты
            not_sent = []
            for chat_id in chats_manager.get_data():
                try:
                    forward_or_copy(chat_id, message)
                except Exception as e:
                    not_sent.append(chat_id)
                    logging.error(f"Something wrong with chat {chat_id}")
                    logging.error(e)
            return not_sent


        def tell_mailing_result(message_id, user, not_sent):  # сообщение инициатору рассылки о ее результате
            successful_count = len(chats_manager.get_data()) - len(not_sent)
            if successful_count == 0:
                result_text = f"❌️ Сообщение не отправлено"
                logging.error(f"Message not sent by @{user.username}")
            elif len(not_sent) == 0:
                result_text = f"✅ Сообщение отправлено во все {beautiful_numeral(successful_count)}"
                logging.info(f"Message sent to all {successful_count} chats by @{user.username}")
            else:
                result_text = ((f"⚠️ Сообщение отправлено в {beautiful_numeral(successful_count)}. "
                               f"Но в еще {beautiful_numeral(len(not_sent))} отправить не получилось: ")
                               + ", ".join(chats_manager.get_data()[chat_id] for chat_id in not_sent))
                logging.error(f"Message sent to {successful_count} chats except {len(not_sent)}: id{not_sent} by @{user.username}")

            bot.send_message(user.id, result_text, reply_to_message_id=message_id)
            return successful_count


        def notify(message, successful_count):  # сообщение всем остальным членам белого списка о рассылке
            if successful_count == 0:
                info_part = f"👆 Это сообщение хотел отправить, но не смог @{message.from_user.username} ({message.from_user.full_name})"
            else:
                info_part = f"👆 Это сообщение в {beautiful_numeral(successful_count)} отправил @{message.from_user.username} ({message.from_user.full_name})"
            for user_id in white_list_manager.get_data():
                try:
                    if user_id == message.from_user.id:
                        continue
                    else:
                        msg = bot.send_message(user_id, message.text, entities=message.entities)
                        bot.send_message(user_id, info_part, reply_to_message_id=msg.id)
                except Exception as e:
                    logging.error(f"Something wrong with member {user_id}")
                    logging.error(e)


        @bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker',
                                            'video', 'video_note', 'voice', 'location', 'contact'],
                             func=lambda message: (message.from_user.id in white_list_manager.get_data() and
                                                   message.chat.type == "private"))
        def make_propagation(message):
            not_sent = repeater(message)
            successful_count = tell_mailing_result(message.id, message.from_user, not_sent)
            notify(message, successful_count)

            # bot.send_message(message.from_user.id,  # TODO: нужно ли подтверждение?
            #                  "Сообщение отправится точно в таком же виде, как вы его написали. Отправить?",
            #                  reply_markup=create_response_markup_type(message.text))


        # def create_response_markup_type(text):
        #     markup = telebot.types.InlineKeyboardMarkup()
        #     markup.add(telebot.types.InlineKeyboardButton("✅ Да, отправить во все чаты", callback_data="{\"action\":\"send\",\"text\":\"" + str(text) + "\"}"),
        #                telebot.types.InlineKeyboardButton("❌ Нет, отмена", callback_data="Cancel"))
        #     return markup
        #
        # @bot.callback_query_handler(func=lambda call: True)
        # def callback(call):
        #     if "send" in call.data:
        #         json_string = json.loads(call.data)
        #         text = json_string['text']
        #
        #         for chat_id in CHATS_LIST:
        #             bot.send_message(chat_id, text)
        #
        #         bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        #         bot.send_message(call.message.chat.id, "✅ Сообщение отправлено во все чаты")
        #     elif call.data == "Cancel":
        #         # bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text)
        #         bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        #         bot.send_message(call.message.chat.id, "Отправка сообщения отменена 👌")

        logging.info("Bot running..")
        bot.polling(none_stop=True)

    except Exception as e:
        logging.error(e)
        bot.stop_polling()

        time.sleep(15)

        logging.info("Running again!")
