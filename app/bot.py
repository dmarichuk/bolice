import asyncio
import uvloop
import datetime as dt

from db import MongoConnection
from pymongo import errors as mongo_errors
from config import (TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN)
from pyrogram import Client, filters, types as pt
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
async def photo_handler(client: Client, message: pt.Message): 
    f = await client.download_media(message.photo, in_memory=True)
    # logger.info(f"Recieved photo from user {message.from_user.id} in chat {message.chat.id}")
    
    img = init_image(f)
    if not img:
        logger.warning("Could not initialize PIL.Image from Telegram photo")
        return
    logger.info("Initialized PIL.Image from telegram photo")
    
    hash = get_phash(img)
    logger.info(f"Obtained image hash: {str(hash)}")

    conn = MongoConnection()
    col = conn[str(message.chat.id)]
    
    try:
        doc = col.insert_one({"img_hash": str(hash), "message_id": message.id, "file_id": message.photo.file_id, "active": True})
        logger.info(f"Inserted document {doc.inserted_id} to db")
    except mongo_errors.DuplicateKeyError:
        logger.warning("Hash already in DB")
        orig_doc = col.find_one({"img_hash": str(hash)})
        await activate_bolice(client, message.chat.id, message, orig_doc)


async def activate_bolice(client: Client, chat_id: int, bayan_msg, orig_doc):
    await client.send_photo(chat_id, photo="./app/static/bolice.jpg", caption="🚨🚨🚨 ЗАМЕЧЕН БАЯН! 🚨🚨🚨", reply_to_message_id=bayan_msg.id)
    await client.send_message(chat_id, reply_to_message_id=orig_doc["message_id"], text="Оригинал")
    countdown = 10
    poll = await client.send_poll(
        chat_id, 
        question="Оправдать?", 
        options=["Виновен", "Невиновен"], 
    )
    
    await edit_inline_button_with_void(client, chat_id, poll.id, countdown)

    while countdown > 0:
        # TODO продумать отображение числа секунд в виде таймера "5:00, 4:59" и тд
        await asyncio.sleep(1)
        countdown -= 1
        if countdown % 10 == 0:
            await edit_inline_button_with_void(client, chat_id, poll.id, countdown)
    
    await client.stop_poll(chat_id, poll.id)
    await edit_inline_button_with_void(client, chat_id, poll.id, "Голосование завершено!")

    updated_poll = await bot_app.get_messages(chat_id, poll.id)
    pro, contra = [option.voter_count for option in updated_poll.poll.options] 
    if execute_sentence(pro, contra):
        punishment_time = 120
        await bot_app.send_photo(chat_id, "./app/static/punish.jpg", reply_to_message_id=updated_poll.id, caption=f"ПРИГОВОРЕН К {punishment_time} СЕКУНДАМ ЗАКЛЮЧЕНИЯ!")
        await bot_app.restrict_chat_member(chat_id, bayan_msg.from_user.id, permissions=pt.ChatPermissions(), until_date=dt.datetime.now() + dt.timedelta(seconds=punishment_time)) # TODO randomize ban time depending on ratio value
    else:
        await bot_app.send_photo(chat_id, "./app/static/justified.jpg", reply_to_message_id=updated_poll.id, caption="ПОЛНОСТЬЮ ОПРАВДАН!") # TODO расширить диапазон картинок для отмены быкования
        # TODO добавить документ картинки в неактивный
 
def execute_sentence(pro, contra):
    try:
        ratio = pro / contra
    except ZeroDivisionError:
        return True
    if ratio <= 1:
        return False
    else:
        return True

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
    bot_app.run()
    # user_app.run(parse_chat_photos(user_app, -1001253753634))