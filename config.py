# config.py
import os

BOT_TOKEN = "8713846517:AAGdPrbhyaG7e3oiYLdiiMllTsCw2HRyAac"
OWNER_ID = int(os.environ.get("OWNER_ID", "7788474071"))
DEV_NAME = "♛𝒀𝑨𝑺𝑰𝑵♛ 𝗸𝗶𝗻𝗴 !"
DEV_USER = "@yacine_ff_39"

KEY_PREFIX = "YAS-KEY"
MAX_DEVICES_DEFAULT = 5

KEYS_FILE = "keys.json"
USERS_FILE = "users.json"
BOT_STATUS_FILE = "bot_status.json"

LANG_EN = "en"
LANG_AR = "ar"

FLASK_PORT = int(os.environ.get("PORT", 5000))
FALLBACK_URL = "http://localhost:5000"