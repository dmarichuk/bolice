import asyncio
import uvloop
import datetime as dt
import random

from db import MongoConnection
from pymongo import errors as mongo_errors
from config import (TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN)
from pyrogram import Client, filters, types as pt
from hash import init_image, get_image_hash
from utils import get_custom_logger, translate_seconds_to_timer


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
async def photo_handler(client: Client, message: pt.Message): 
    f = await client.download_media(message.photo, in_memory=True)
    # logger.info(f"Recieved photo from user {message.from_user.id} in chat {message.chat.id}")
    
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
        doc = col.insert_one({"img_hash": str(hash), "message_id": message.id, "file_id": message.photo.file_id, "is_active": True})
        logger.info(f"Inserted document {doc.inserted_id} to db")
    except mongo_errors.DuplicateKeyError:
        if col.find_one({"img_hash": str(hash), "is_active": True}):
            logger.warning("Hash already in DB")
            orig_doc = col.find_one({"img_hash": str(hash)})
            await activate_bolice(client, message.chat.id, message, orig_doc)
        else:
            logger.info(f"Hash {hash} is deactivated")


async def activate_bolice(client: Client, chat_id: int, bayan_msg, orig_doc):
    logger.info("Bolice activated in chat", chat_id, "MSG_ID", bayan_msg.id, "DOC ID", orig_doc["_id"])
    await client.send_photo(chat_id, photo="./app/static/bolice.jpg", caption="🚨🚨 ЗАМЕЧЕН БАЯН! 🚨🚨", reply_to_message_id=bayan_msg.id)
    await client.send_message(chat_id, reply_to_message_id=orig_doc["message_id"], text="Оригинал")
    
    logger.info("Poll is activated")
    countdown = 300
    poll = await client.send_poll(
        chat_id, 
        question="Оправдать?", 
        options=["Виновен", "Невиновен"],
        is_anonymous=False
    )
    await edit_inline_button_with_void(client, chat_id, poll.id, f"Осталось {translate_seconds_to_timer(countdown)}")

    while countdown > 0:
        await asyncio.sleep(1)
        countdown -= 1
        if countdown % 10 == 0:
            await edit_inline_button_with_void(client, chat_id, poll.id, f"Осталось {translate_seconds_to_timer(countdown)}")
    
    await client.stop_poll(chat_id, poll.id, pt.InlineKeyboardMarkup([
            [pt.InlineKeyboardButton("Голосование завершено!", "void")]
        ]))
    updated_poll = await bot_app.get_messages(chat_id, poll.id)
    pro, contra = [option.voter_count for option in updated_poll.poll.options]
    logger.info(f"Poll is closed. PRO {pro}, CONTRA {contra}")
    
    guilty, punishment_time = execute_sentence(pro, contra)
    if guilty:
        logger.info(f"{bayan_msg.from_user.id} is guilty. Execute punishment for {punishment_time}")
        await bot_app.send_photo(chat_id, "./app/static/punish.jpg", reply_to_message_id=updated_poll.id, caption=f"ПРИГОВОРЕН К ЗАКЛЮЧЕНИЮ ЗА БАЯНЫ! ВРЕМЯ ЗАКЛЮЧЕНИЯ - {translate_seconds_to_timer(punishment_time)}")
        await bot_app.restrict_chat_member(chat_id, bayan_msg.from_user.id, permissions=pt.ChatPermissions(), until_date=dt.datetime.now() + dt.timedelta(seconds=punishment_time))
    else:
        logger.info(f"{bayan_msg.from_user.id} is innocent. Punishment time is {punishment_time}")
        await bot_app.send_photo(chat_id, "./app/static/justified.jpg", reply_to_message_id=updated_poll.id, caption="ПОЛНОСТЬЮ ОПРАВДАН!")
        conn = MongoConnection()
        col = conn[str(chat_id)]
        updated_doc = col.find_one_and_update({"img_hash": orig_doc["img_hash"]}, {"$set": {"is_active": False}})
        logger.info(f"Deactivated document {updated_doc['_id']}")
 
def execute_sentence(pro, contra):
    try:
        ratio = contra / pro
    except ZeroDivisionError:
        return False, 0
    if ratio > 1:
        return False, 0
    else:
        punishment_time = get_punishment_time(ratio)
        return True, punishment_time

def get_punishment_time(ratio):
    random.seed(dt.datetime.now().second)
    if ratio == 0:
        return random.randint(60 * 15, 60 * 60 - 1)
    if ratio <= 0.33:
        return random.randint(60 * 10, 60 * 15)
    if ratio <= 0.66:
        return random.randint(60 * 5, 60 * 10)
    if ratio <= 1:
        return random.randint(60, 60 * 5)

    
async def edit_inline_button_with_void(client, chat_id, msg_id, data):
    await client.edit_message_reply_markup(chat_id, msg_id, reply_markup=pt.InlineKeyboardMarkup([
            [pt.InlineKeyboardButton(data, "void")]
        ]))


@bot_app.on_callback_query()  
async def void(_, __):
    pass
    
async def parse_chat_photos(client, chat_id):
    conn = MongoConnection()
    col = conn[str(chat_id)]

    async with client:
        async for msg in client.get_chat_history(chat_id):
            if msg.photo:
                f = await client.download_media(msg.photo, in_memory=True)
                img = init_image(f)
                hash = get_image_hash(img)
                try:
                    doc = col.insert_one({"img_hash": str(hash), "message_id": msg.id, "file_id": msg.photo.file_id, "active": True})
                    logger.info(f"Inserted document {doc.inserted_id} to db")
                except mongo_errors.DuplicateKeyError:
                    logger.warning("Hash already in DB")

                    logger.info("Getting duplicate image")
                    bayan = col.find_one_and_update({"img_hash": str(hash)}, {"$set": {"message_id": msg.id}})
                    
                    logger.info("Creating directory and save collisions")
                    dir_name = f'{msg.id}_{bayan["message_id"]}'
                    await client.download_media(msg.photo, f"./media/collisions/{dir_name}/")
                    await client.download_media(bayan["file_id"], f"./media/collisions/{dir_name}/")
                

if __name__ == "__main__":
    bot_app.run()
    # user_app.run(parse_chat_photos(user_app, -1001253753634))