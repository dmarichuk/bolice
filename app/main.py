import asyncio

import uvloop
from pymongo import errors as mongo_errors
from pyrogram import Client, filters
from pyrogram import types as pt

from bot.common import edit_inline_button_with_void
from bot.parse import parse_chat_photos
from bot.punish import activate_bolice
from bot.search import search_for_similarity
from config import (BASE_DIR, D_DISK_CHAT_ID, TELEGRAM_API_HASH,
                    TELEGRAM_API_ID, TELEGRAM_BOT_TOKEN)
from db import MongoConnection
from hash import get_image_hash, init_image
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


@bot_app.on_message(filters.regex("!поиск"))
async def search_handler(client: Client, message: pt.Message):
    if not message.reply_to_message_id:
        return await message.reply(
            "Для выполнения поиска, введите команду в ответ на сообщение с возможным баяном"
        )

    if not message.reply_to_message.photo:
        return await message.reply("В прикрепленном сообщении нет фото!")

    conn = MongoConnection(str(message.chat.id))
    col = await conn.get_history_collection()
    suspected_doc = await col.find_one({"message_id": message.reply_to_message_id})
    if not suspected_doc:
        return await message.reply(
            "Не могу найти это сообщение в базе! Пишите админу(он вряд ли ответит)"
        )

    hash_to_search = suspected_doc["img_hash"]
    cursor = col.find()

    logger.info("Started to look for a similar hash...")

    answer = await client.send_photo(
        message.chat.id,
        photo="./static/search.jpg",
        reply_to_message_id=message.id,
    )

    await edit_inline_button_with_void(
        client, message.chat.id, answer.id, f"Идет поиск..."
    )

    try:
        similarities = await asyncio.wait_for(
            search_for_similarity(hash_to_search, cursor), timeout=30
        )
    except asyncio.exceptions.TimeoutError:
        logger.warning("Search exceeded time limit!")
        return await message.reply("Что то я долго думаю, отдохну пожалуй")

    await edit_inline_button_with_void(
        client, message.chat.id, answer.id, f"Поиск завершен!"
    )

    if len(similarities) > 0:
        for proximity, similarity_msg_id, is_active in similarities:
            if proximity == 0:
                similarity = "оригинал"
            elif proximity < 0.01:
                similarity = "99.99%"
            else:
                similarity = f"{(100 - proximity):.2f}%"
            msg = f"Схожесть: {similarity}"
            if not is_active:
                msg += "\nСтатус: Деактивирована"
            await client.send_message(
                message.chat.id,
                msg,
                reply_to_message_id=similarity_msg_id,
            )
        return

    await message.reply("Похожих картинок не обнаружено!")


@bot_app.on_message(
    ~filters.me
    & (
        (
            filters.photo & filters.linked_channel
        )  # Photos redirected from linked channel
        | (
            filters.photo & ~filters.forwarded & ~filters.channel
        )  # Photos from users in channel chat
    )
)
async def photo_handler(client: Client, message: pt.Message):
    f = await client.download_media(message.photo, in_memory=True)

    img = init_image(f)
    if not img:
        logger.warning("Could not initialize PIL.Image from Telegram photo")
        return
    logger.info("Initialized PIL.Image from telegram photo")

    hash = get_image_hash(img)
    logger.info(f"Obtained image hash: {str(hash)}")

    conn = MongoConnection(str(message.chat.id))
    col = await conn.get_history_collection()

    try:
        doc = await col.insert_one(
            {
                "img_hash": str(hash),
                "message_id": message.id,
                "file_id": message.photo.file_id,
                "is_active": True,
            }
        )
        logger.info(f"Inserted document {doc.inserted_id} to db")
    except mongo_errors.DuplicateKeyError:
        active = await col.find_one({"img_hash": str(hash), "is_active": True})
        if active:
            logger.warning("Hash already in DB")
            orig_doc = await col.find_one({"img_hash": str(hash)})
            await activate_bolice(client, message.chat.id, message, orig_doc)
        else:
            logger.info(f"Hash {hash} is deactivated")


@bot_app.on_callback_query()
async def void(_, __):
    pass


if __name__ == "__main__":
    import sys

    sys.path.append(BASE_DIR)

    if len(sys.argv) == 1 or sys.argv[1] == "run_bot":
        bot_app.run()
    elif len(sys.argv) == 3 and sys.argv[1] == "parse_chat":
        chat_id = int(sys.argv[2])
        user_app.run(parse_chat_photos(user_app, chat_id))
    else:
        sys.stderr.write(f"Can't parse argument {sys.argv[1]!r}\n")
