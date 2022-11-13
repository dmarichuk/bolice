from decouple import config

BUILD_TYPE = config("BUILD_TYPE")

match BUILD_TYPE:
    case "DEV":
        TELEGRAM_API_ID = config("DEV_TELEGRAM_API_ID", cast=int)
        TELEGRAM_API_HASH = config("DEV_TELEGRAM_API_HASH")
        TELEGRAM_BOT_TOKEN = config("DEV_TELEGRAM_BOT_TOKEN")
    case "PROD":
        TELEGRAM_API_ID = config("TELEGRAM_API_ID", cast=int)
        TELEGRAM_API_HASH = config("TELEGRAM_API_HASH")
        TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")

D_DISK_CHAT_ID = config("D_DISK_CHAT_ID")
MONGO_USERNAME = config("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = config("MONGO_INITDB_ROOT_PASSWORD")
MONGO_HOST = config("MONGO_HOST")
