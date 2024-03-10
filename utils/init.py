import logging
import telebot
from utils.secret import *
from utils.filehandling import *

bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(module)s - %(levelname)s: %(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(logfile_name),
        logging.StreamHandler()
    ],
    datefmt='%d/%b %H:%M:%S',
)

BOT_ID = bot.get_me().id
ADMIN_ID = admin

white_list_manager = ListManager("data/white_list.json")
chats_manager = ListManager("data/chats.json")
messages_manager = ListManager("data/messages.json")
logging.info(f"Data loaded from files")