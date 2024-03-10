import time
from datetime import datetime

from utils.init import *
from utils.commands import *
from utils.other import beautiful_numeral

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

            btn1 = telebot.types.InlineKeyboardButton("📢 Отправить новое сообщение", callback_data="send")
            btn2 = telebot.types.InlineKeyboardButton("✏️ Изменить предыдущее сообщение", callback_data="edit")
            btn3 = telebot.types.InlineKeyboardButton("🪓 Удалить предыдущее сообщение", callback_data="delete")

            markup.add(btn1)
            markup.add(btn2)
            markup.add(btn3)

            return markup

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
                return bot.forward_message(chat_id, message.chat.id, message.id)
            else:
                return bot.copy_message(chat_id, message.chat.id, message.id)


        def repeater(message):  # непосредственно отправка сообщения во все чаты
            not_sent = []

            chat_ids = []
            msg_ids = []
            for chat_id in chats_manager.get_data():
                try:
                    msg_id = forward_or_copy(chat_id, message).message_id
                    chat_ids.append(chat_id)
                    msg_ids.append(msg_id)
                except Exception as e:
                    not_sent.append(chat_id)
                    logging.error(f"Something wrong with chat {chat_id}")
                    logging.error(e)
            messages_manager.add_data(hash(message), {"chat_ids": chat_ids, "msg_ids": msg_ids})
            return not_sent


        def tell_mailing_result(message_id, message_hash, user, not_sent):  # сообщение инициатору рассылки о ее результате
            successful_count = len(chats_manager.get_data()) - len(not_sent)
            if successful_count == 0:
                result_text = f"❌️ Сообщение не отправлено"
                logging.error(f"Message not sent by @{user.username}")
            elif len(not_sent) == 0:
                result_text = f"✅ Сообщение отправлено во все {beautiful_numeral(successful_count)}"
                logging.info(f"Message sent to all {successful_count} chats by @{user.username}")
            else:
                result_text = ((f"⚠️ Сообщение отправлено в {beautiful_numeral(successful_count)}. "
                                f"Но еще в {beautiful_numeral(len(not_sent))} отправить не получилось: ")
                               + ", ".join(chats_manager.get_data()[chat_id] for chat_id in not_sent))
                logging.error(
                    f"Message sent to {successful_count} chats except {len(not_sent)}: id{not_sent} by @{user.username}")

            result_text += f"\n\nИдентификатор этой рассылки: <code>{message_hash}</code>"
            bot.send_message(user.id, result_text, reply_to_message_id=message_id, parse_mode="HTML")
            return successful_count


        def notify(message, successful_count):  # сообщение всем остальным членам белого списка о рассылке
            if successful_count == 0:
                info_part = f"👆 Это сообщение хотел отправить, но не смог @{message.from_user.username} ({message.from_user.full_name})"
            else:
                info_part = f"👆 Это сообщение в {beautiful_numeral(successful_count)} отправил @{message.from_user.username} ({message.from_user.full_name})"
            info_part += f"\n\nИдентификатор этой рассылки: <code>{hash(message)}</code>"
            for user_id in white_list_manager.get_data():
                try:
                    if user_id == message.from_user.id:
                        continue
                    else:
                        msg = bot.send_message(user_id, message.text, entities=message.entities)
                        bot.send_message(user_id, info_part, reply_to_message_id=msg.id, parse_mode="HTML")
                except Exception as e:
                    logging.error(f"Something wrong with member {user_id}")
                    logging.error(e)


        def make_propagation(message):
            if message.text == "/cancel":
                logging.info(f"Cancel message from user @{message.from_user.username}")
                bot.send_message(message.chat.id, "Отменено")
                return
            not_sent = repeater(message)
            successful_count = tell_mailing_result(message.id, hash(message), message.from_user, not_sent)
            notify(message, successful_count)


        def too_late(message):
            if 23 <= datetime.now().hour or datetime.now().hour < 7:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id,
                                 "Сейчас ночь, все спят. Вы уверены, что хотите отправить сообщение прямо сейчас?",
                                 reply_markup=create_confirmation_markup())
                return True
            else:
                return False


        def create_confirmation_markup():
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("✅ Да", callback_data="send_now"),
                       telebot.types.InlineKeyboardButton("❌ Нет, отмена", callback_data="сancel"))
            return markup

        def delete_propagation(message):
            if message.text == "/cancel":
                logging.info(f"Cancel message from user @{message.from_user.username}")
                bot.send_message(message.chat.id, "Отменено")
                return
            try:
                message_hash = int(message.text)
                this_message = messages_manager.get_data()[message_hash]
                for chat_id, msg_id in zip(this_message["chat_ids"], this_message["msg_ids"]):
                    bot.delete_message(chat_id, msg_id)
                messages_manager.del_data(message_hash)
                bot.send_message(message.chat.id, "Удалено", reply_to_message_id=message.message_id)
                logging.info(f"Message deleted by @{message.from_user.username}")
            except KeyError:
                bot.send_message(message.chat.id, "Рассылки с таким идентификатором не существует", reply_to_message_id=message.message_id)
                logging.error(f"Message not found by @{message.from_user.username}")
            except Exception as e:
                logging.error(f"Something wrong when @{message.from_user.username} tried to delete message with hash {message_hash}")
                logging.error(e)

        def edit_propagation2(new_message, this_message):
            if new_message.text == "/cancel":
                logging.info(f"Cancel message from user @{new_message.from_user.username}")
                bot.send_message(new_message.chat.id, "Отменено")
                return
            try:
                for chat_id, msg_id in zip(this_message["chat_ids"], this_message["msg_ids"]):
                    bot.edit_message_text(chat_id=chat_id, message_id=msg_id,
                                          text=new_message.text, entities=new_message.entities)
                # messages_manager.del_data(hash(this_message))  # TODO: надо ли менять хэш?
                # messages_manager.add_data(hash(message), {"chat_ids": this_message["chat_ids"], "msg_ids": this_message["msg_ids"]})
                bot.send_message(new_message.chat.id, "Изменено", reply_to_message_id=new_message.message_id)
                logging.info(f"Message edited by @{new_message.from_user.username}")
            except Exception as e:
                logging.error(f"Something wrong when @{new_message.from_user.username} tried to edit message")
                logging.error(e)

        def edit_propagation1(message):
            if message.text == "/cancel":
                logging.info(f"Cancel message from user @{message.from_user.username}")
                bot.send_message(message.chat.id, "Отменено")
                return
            try:
                message_hash = int(message.text)
                this_message = messages_manager.get_data()[message_hash]
                bot.send_message(message.chat.id, "Напишите новый текст сообщения")
                bot.register_next_step_handler(message, lambda new_message: edit_propagation2(new_message, this_message))
            except KeyError:
                bot.send_message(message.chat.id, "Рассылки с таким идентификатором не существует", reply_to_message_id=message.message_id)
                logging.error(f"Message not found by @{message.from_user.username}")
            except Exception as e:
                logging.error(f"Something wrong when @{message.from_user.username} tried to edit message with hash {message_hash}")
                logging.error(e)

        @bot.callback_query_handler(func=lambda call: True)
        def callback(call):
            if call.data == "send_now" or (call.data == "send" and not too_late(call.message)):
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text="Напишите сообщение, которое будет отправлено во все чаты")
                    bot.register_next_step_handler(call.message, make_propagation)
            elif call.data == "сancel":
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Отправка сообщения отменена 👌")
            elif call.data == "delete":
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Напишите идентификатор рассылки, которую хотите удалить")
                bot.register_next_step_handler(call.message, delete_propagation)
            elif call.data == "edit":
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text="Напишите идентификатор рассылки, текст в которой хотите изменить")
                bot.register_next_step_handler(call.message, edit_propagation1)





        logging.info("Bot running..")
        bot.polling(none_stop=True)

    except Exception as e:
        logging.error(e)
        bot.stop_polling()

        time.sleep(15)

        logging.info("Running again!")
