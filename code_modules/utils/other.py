from code_modules.utils.init import *


def translate_action(action_type: ActionType, tense="past"):
    translated_actions = {
        ActionType.SEND: {"past": "отправлено", "future": "отправить"},
        ActionType.EDIT: {"past": "изменено", "future": "изменить"},
        ActionType.DELETE: {"past": "удалено", "future": "удалить"}
    }
    try:
        return translated_actions[action_type][tense]
    except KeyError:
        logging.error(f"Неизвестное action_type/tense = {action_type}/{tense}")


def beautiful_numeral(action_type: ActionType, n):
    # send: отправлено в 1 чат, отправлено в 2 чата, отправлено в 5 чатов
    # edit: изменено в 1 чате, изменено в 2/5 чатах
    # delete: удалено из 1 чата, удалено из 2/5 чатов

    result = str(n)

    match action_type:
        case ActionType.SEND:
            if 5 < n % 100 < 21:
                result += " чатов"
            elif n % 10 == 1:
                result += " чат"
            elif 2 <= n % 10 <= 4:
                result += " чата"
            else:
                result += " чатов"
        case ActionType.EDIT:
            if n % 10 == 1 and n % 100 != 11:
                result += " чате"
            else:
                result += " чатах"
        case ActionType.DELETE:
            if n % 10 == 1 and n % 100 != 11:
                result += " чата"
            else:
                result += " чатов"

    return result


def beautiful_action(action_type: ActionType, successful_count, not_successful_count):
    if successful_count == 0:
        result = f"❌ Сообщение не {translate_action(action_type)}"
    elif not_successful_count == 0:
        result = f"✅ Сообщение {translate_action(action_type)}"
        if action_type is ActionType.SEND: result += ' во все'
        elif action_type is ActionType.EDIT: result += ' во всех'
        elif action_type is ActionType.DELETE: result += ' из всех'
        result += f" {beautiful_numeral(action_type, successful_count)}"
    else:
        result = f"⚠️ Сообщение {translate_action(action_type)}"
        preposition = 'из' if action_type is ActionType.DELETE else 'в'
        result += f" {preposition} {beautiful_numeral(action_type, successful_count)}. " \
                  f"Но еще {preposition} {beautiful_numeral(action_type, not_successful_count)} {translate_action(action_type, tense='future')} не получилось: "
    return result


def forward_or_copy(chat_id, message):  # TODO: пересылка сообщений с несколькими медиа
    if message.forward_from_chat or message.content_type == "poll":  # пересылка только опросов и сообщений из каналов
        return bot.forward_message(chat_id, message.chat.id, message.id)
    else:
        return bot.copy_message(chat_id, message.chat.id, message.id)