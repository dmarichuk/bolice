from decouple import config
import os

TELEGRAM_API_ID = config(os.environ.get("TELEGRAM_API_ID"), cast=int)
TELEGRAM_API_HASH = config(os.environ.get("TELEGRAM_API_HASH"))
TELEGRAM_BOT_TOKEN = config(os.environ.get("TELEGRAM_BOT_TOKEN"))

MONGO_HOST = config(os.environ.get("MONGO_INITDB_HOST"))
MONGO_PORT = config(os.environ.get("MONGO_INITDB_PORT"))
MONGO_USERNAME = config(os.environ.get("MONGO_INITDB_ROOT_USERNAME"))
MONGO_PASSWORD = config(os.environ.get("MONGO_INITDB_ROOT_PASSWORD"))
