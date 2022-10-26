import io
import asyncio

from db import MongoConnection
from config import (TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN)
from pyrogram import Client, filters
from hash import init_image, get_phash
from utils import get_custom_logger


logger = get_custom_logger("bot")

app = Client(
    "agressive_d_disk_bot",
    api_id=TELEGRAM_API_ID, 
    api_hash=TELEGRAM_API_HASH, 
    bot_token=TELEGRAM_BOT_TOKEN,
    in_memory=True
)


@app.on_message(filters.photo)
async def photo_handler(client, message): 
    f = await client.download_media(message.photo, in_memory=True)
    logger.info(f"Recieved photo from user {message.from_user.id} in chat {message.chat.id}")
    
    img = init_image(f)
    if not img:
        logger.warning("Could not initialize PIL.Image from Telegram photo")
        return
    logger.info("Initialized PIL.Image from telegram photo")
    
    hash = get_phash(img)
    logger.info(f"Obtained image hash: {str(hash)}")

    conn = MongoConnection()
    col = conn[message.chat.id]
    doc = col.insert_one({"img_hash": str(hash), "message_id": message.id, "active": True})
    logger.info(f"Inserted document {doc} to db")
    
if __name__ == "__main__":
    app.run()    