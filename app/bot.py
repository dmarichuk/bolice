import asyncio
import uvloop
import os

from db import MongoConnection
from pymongo import errors as mongo_errors
from config import (TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN)
from pyrogram import Client, filters
from hash import init_image, get_phash
from utils import get_custom_logger


logger = get_custom_logger("bot")
uvloop.install()

user_app = Client(
    "bolice_user",
    api_id=TELEGRAM_API_ID, 
    api_hash=TELEGRAM_API_HASH
)

bot_app = Client(
    "bolice_bot",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH,
    bot_token=TELEGRAM_BOT_TOKEN,
    in_memory=True
)

@bot_app.on_message(filters.photo)
async def photo_handler(client, message): 
    f = await client.download_media(message.photo, in_memory=True)
    # logger.info(f"Recieved photo from user {message.from_user.id} in chat {message.chat.id}")
    
    img = init_image(f)
    if not img:
        logger.warning("Could not initialize PIL.Image from Telegram photo")
        return
    logger.info("Initialized PIL.Image from telegram photo")
    
    hash = get_phash(img)
    logger.info(f"Obtained image hash: {str(hash)}")

    # conn = MongoConnection()
    # col = conn[message.chat.id]
    # doc = col.insert_one({"img_hash": str(hash), "message_id": message.id, "active": True})
    # logger.info(f"Inserted document {doc} to db")

    
async def parse_chat_photos(client, chat_id):
    conn = MongoConnection()
    col = conn[str(chat_id)]

    async with client:
        async for msg in client.get_chat_history(chat_id):
            if msg.photo:
                f = await client.download_media(msg.photo, in_memory=True)
                img = init_image(f)
                hash = get_phash(img)
                try:
                    doc = col.insert_one({"img_hash": str(hash), "message_id": msg.id, "file_id": msg.photo.file_id, "active": True})
                    logger.info(f"Inserted document {doc} to db")
                except mongo_errors.DuplicateKeyError:
                    logger.warning("Hash already in DB")

                    logger.info("Getting duplicate image")
                    dup_doc = col.find_one({"img_hash": str(hash)})
                    
                    logger.info("Creating directory and save collisions")
                    dir_name = f'{msg.id}_{dup_doc["message_id"]}'
                    await client.download_media(msg.photo, f"./media/collisions/{dir_name}/")
                    await client.download_media(dup_doc["file_id"], f"./media/collisions/{dir_name}/")
                

if __name__ == "__main__":
    # bot_app.run()
    user_app.run(parse_chat_photos(user_app, -1001253753634))