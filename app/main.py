import uvloop
from bot import activate_bolice, parse_chat_photos
from config import (D_DISK_CHAT_ID, TELEGRAM_API_HASH, TELEGRAM_API_ID,
                    TELEGRAM_BOT_TOKEN)
from db import MongoConnection
from hash import get_image_hash, init_image
from pymongo import errors as mongo_errors
from pyrogram import Client, filters
from pyrogram import types as pt
from utils import get_custom_logger

logger = get_custom_logger("main")
uvloop.install()

user_app = Client("bolice_user", api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH)

bot_app = Client(
    "bolice_bot",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH,
    bot_token=TELEGRAM_BOT_TOKEN,
    in_memory=True,
)


@bot_app.on_message(filters.photo & ~filters.forwarded)
async def photo_handler(client: Client, message: pt.Message):
    f = await client.download_media(message.photo, in_memory=True)

    img = init_image(f)
    if not img:
        logger.warning("Could not initialize PIL.Image from Telegram photo")
        return
    logger.info("Initialized PIL.Image from telegram photo")

    hash = get_image_hash(img)
    logger.info(f"Obtained image hash: {str(hash)}")

    conn = MongoConnection()
    col = conn[str(message.chat.id)]

    try:
        doc = col.insert_one(
            {
                "img_hash": str(hash),
                "message_id": message.id,
                "file_id": message.photo.file_id,
                "is_active": True,
            }
        )
        logger.info(f"Inserted document {doc.inserted_id} to db")
    except mongo_errors.DuplicateKeyError:
        if col.find_one({"img_hash": str(hash), "is_active": True}):
            logger.warning("Hash already in DB")
            orig_doc = col.find_one({"img_hash": str(hash)})
            await activate_bolice(client, message.chat.id, message, orig_doc)
        else:
            logger.info(f"Hash {hash} is deactivated")


@bot_app.on_callback_query()
async def void(_, __):
    pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1 or sys.argv[1] == "run_bot":
        bot_app.run()
    elif sys.argv[1] == "parse_d_disk":
        user_app.run(parse_chat_photos(user_app, D_DISK_CHAT_ID))
    else:
        sys.stderr.write(f"Can't parse argument {sys.argv[1]!r}\n")
