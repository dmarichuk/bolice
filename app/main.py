import io
import asyncio
from operator import methodcaller

import uvloop
from bot.common import define_user_from_message, edit_inline_button_with_void
from bot.parse import parse_chat_photos
from bot.punish import activate_bolice, activate_execution, get_judgment_poll
from bot.search import search_for_similarity
from bot.users import get_user_from_chat
from config import (BASE_DIR, POLL_TIMER, TELEGRAM_API_HASH, TELEGRAM_API_ID,
                    TELEGRAM_BOT_TOKEN, QUEUE_NAME)
from db import MongoConnection
from hash import get_image_hash, init_image
from pymongo import errors as mongo_errors
from pyrogram import Client, filters
from pyrogram import types as pt
from broker import redis_db
from utils import get_custom_logger, translate_seconds_to_timer

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

BOT_USER = None


@bot_app.on_message(filters.regex("^!суд"))
async def trial_handler(client: Client, message: pt.Message):
    """!суд @username <обвинение>"""
    logger.info("Trial started")
    parsed_message = message.text.split(" ")
    match parsed_message:
        case [_, username]:
            accusation = "Плохое поведение"
        case [_, username, *accusation]:
            accusation = " ".join(accusation)
        case _:
            return await message.reply(
                "Не могу распознать команду\nВводите команду вида: !суд @username <обвинение>"
            )
    logger.info(f"Parsed message {parsed_message}")
    conn = MongoConnection(message.chat.id)

    pt_prosecutor = define_user_from_message(message)
    prosecutor = await get_user_from_chat(pt_prosecutor, message.chat.id, client, conn)
    defendant = await get_user_from_chat(username, message.chat.id, client, conn)

    global BOT_USER
    if not BOT_USER:
        BOT_USER = await client.get_me()

    logger.info(f"Prosecutor {prosecutor}")
    logger.info(f"Defendant {defendant}")

    trial_available, delta = prosecutor.is_trial_available()
    if not trial_available:
        logger.error(f"Trial limit encountered. Delta: {delta}")
        return await message.reply(
            f"Вы достигли лимита по вызову суда! Осталось ещё {translate_seconds_to_timer(15 * 60 - delta)} до новой попытки"
        )

    if defendant.username == BOT_USER.username:
        logger.error("Trial against bolice")
        return await activate_execution(
            client,
            message.chat.id,
            prosecutor,
            1,
            1,
            "ДУМАЕШЬ УМНЫЙ ТАКОЙ, ДА? ПОСИДИ-КА!\n",
            None,
            reply_to=message,
        )

    if defendant == prosecutor:
        logger.error("Trial against self")
        return await message.reply("Вы не можете судиться против себя!")

    if defendant.on_trial:
        logger.error("User already on trial")
        return await message.reply("Этот пользователь уже учавствует в суде!")

    defendant.on_trial = True
    prosecutor.last_poll = message.date.timestamp()
    await prosecutor.to_db(message.chat.id, conn)
    await defendant.to_db(message.chat.id, conn)

    await client.send_photo(
        message.chat.id,
        photo="./static/trial.jpg",
        reply_to_message_id=message.id,
    )

    is_executed = get_judgment_poll(
        client, message.chat.id, defendant, accusation, POLL_TIMER
    )
    await asyncio.wait_for(is_executed, None)
    defendant.on_trial = False
    await defendant.to_db(message.chat.id, conn)


@bot_app.on_message(filters.regex("^!поиск"))
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
        logger.info("Message not in database, initializing image")
        f = await client.download_media(message.reply_to_message.photo, in_memory=True)
        img = init_image(f)
        img_hash = get_image_hash(img)

    hash_to_search = suspected_doc["hash"] if suspected_doc else str(img_hash)
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
                similarity = "~99.99%"
            else:
                similarity = f"{100 * (1 - proximity):.2f}%"
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
                "hash": str(hash),
                "message_id": message.id,
                "file_id": message.photo.file_id,
                "is_active": True,
            }
        )
        logger.info(f"Inserted document {doc.inserted_id} to db")
    except mongo_errors.DuplicateKeyError:
        active = await col.find_one({"hash": str(hash), "is_active": True})
        if active:
            logger.warning("Hash already in DB")
            orig_doc = await col.find_one({"hash": str(hash)})
            await activate_bolice(client, message.chat.id, message, orig_doc)
        else:
            logger.info(f"Hash {hash} is deactivated")


@bot_app.on_message(filters.regex("^!хочумем"))
async def get_meme_from_queue(client, message):
    f = await redis_db.rpop(QUEUE_NAME)
    if f:
        await client.send_photo(
            message.chat.id,
            io.BytesIO(bytes(f)),
            reply_to_message_id=message.id,
        )
    else:
        await client.send_message(message.chat.id, "Мемов пока нет")


@bot_app.on_message(filters.regex("^!скока"))
async def get_len_of_memes(client, message):
    length = await redis_db.llen(QUEUE_NAME)
    await client.send_message(message.chat.id, f"Мемов в очереди: {length}")


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
