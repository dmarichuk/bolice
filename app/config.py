from pathlib import Path

from decouple import config

BASE_DIR = Path.cwd()
BUILD_TYPE = config("BUILD_TYPE")

match BUILD_TYPE:
    case "DEV":
        TELEGRAM_API_ID = config("DEV_TELEGRAM_API_ID", cast=int)
        TELEGRAM_API_HASH = config("DEV_TELEGRAM_API_HASH")
        TELEGRAM_BOT_TOKEN = config("DEV_TELEGRAM_BOT_TOKEN")
        DEV_CHAT = config("DEV_CHAT", cast=int)
        POLL_TIMER = 0.5 * 60
        TRIAL_LIMIT = 0.5 * 60
    case "PROD":
        TELEGRAM_API_ID = config("TELEGRAM_API_ID", cast=int)
        TELEGRAM_API_HASH = config("TELEGRAM_API_HASH")
        TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
        POLL_TIMER = 5 * 60
        TRIAL_LIMIT = 15 * 60

D_DISK_CHAT_ID = config("D_DISK_CHAT_ID", cast=int)
MONGO_USERNAME = config("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = config("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = config("MONGO_HOST")
SIMILARITY_LIMIT = 0.25
HASH_SIZE = 64
