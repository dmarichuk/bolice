import asyncio
import datetime as dt
import random

from config import D_DISK_CHAT_ID
from db import MongoConnection
from hash import get_image_hash, init_image
from pymongo import errors as mongo_errors
from pyrogram import Client
from pyrogram import types as pt
from utils import get_custom_logger, translate_seconds_to_timer

logger = get_custom_logger("bot")


async def activate_bolice(client: Client, chat_id: int, bayan_msg, orig_doc):
    logger.info(f"Bolice activated in chat {chat_id}. Message id {bayan_msg.id}, Document id {orig_doc['_id']}")
    await client.send_photo(
        chat_id,
        photo="./static/bolice.jpg",
        caption="🚨🚨 ЗАМЕЧЕН БАЯН! 🚨🚨",
        reply_to_message_id=bayan_msg.id,
    )
    await client.send_message(
        chat_id, reply_to_message_id=orig_doc["message_id"], text="Оригинал"
    )
    logger.info("Poll is activated")
    countdown = 300
    poll = await client.send_poll(
        chat_id,
        question="Оправдать?",
        options=["Виновен", "Невиновен"],
        is_anonymous=False,
    )
    await edit_inline_button_with_void(
        client, chat_id, poll.id, f"Осталось {translate_seconds_to_timer(countdown)}"
    )

    while countdown > 0:
        await asyncio.sleep(1)
        countdown -= 1
        if countdown % 10 == 0:
            await edit_inline_button_with_void(
                client,
                chat_id,
                poll.id,
                f"Осталось {translate_seconds_to_timer(countdown)}",
            )

    await client.stop_poll(
        chat_id,
        poll.id,
        pt.InlineKeyboardMarkup(
            [[pt.InlineKeyboardButton("Голосование завершено!", "void")]]
        ),
    )
    updated_poll = await client.get_messages(chat_id, poll.id)
    pro, contra = [option.voter_count for option in updated_poll.poll.options]
    logger.info(f"Poll is closed. PRO {pro}, CONTRA {contra}")
    sender = define_user_from_message(bayan_msg)
    if sender is not None:
        logger.info(f"Bayan sender - {sender}")
        is_executed = await activate_execution(
            client,
            chat_id,
            sender,
            pro,
            contra,
            "ПРИГОВОРЕН К ЗАКЛЮЧЕНИЮ ЗА БАЯНЫ!",
            "ПОЛНОСТЬЮ ОПРАВДАН",
            updated_poll,
        )
        if not is_executed:
            conn = MongoConnection()
            col = conn[str(chat_id)]
            updated_doc = col.find_one_and_update(
                {"img_hash": orig_doc["img_hash"]}, {"$set": {"is_active": False}}
            )
            logger.info(f"Deactivated document {updated_doc['_id']}")
    else:
        logger.error(f"Sender is None from message {bayan_msg}")


def define_user_from_message(msg: pt.Message) -> pt.User | pt.Chat:
    if msg.from_user:
        return msg.from_user
    if msg.sender_chat:
        return msg.sender_chat
    return None


async def activate_execution(
    client: Client,
    chat_id: int,
    user: pt.User | pt.Chat,
    pro: int,
    contra: int,
    punishment_caption: str | None = None,
    justified_caption: str | None = None,
    reply_to: pt.Message | None = None,
) -> bool:
    guilty, punishment_time = execute_sentence(pro, contra)
    if guilty:
        logger.info(f"{user.id} is guilty. Execute punishment for {punishment_time}")
        await client.send_photo(
            chat_id,
            "./static/punish.jpg",
            reply_to_message_id=reply_to.id,
            caption=f"{punishment_caption} ВРЕМЯ ЗАКЛЮЧЕНИЯ - {translate_seconds_to_timer(punishment_time)}",
        )
        match user:
            case pt.User:
                await client.restrict_chat_member(
                    chat_id,
                    user.id,
                    permissions=pt.ChatPermissions(),
                    until_date=dt.datetime.now()
                    + dt.timedelta(seconds=punishment_time),
                )
            case pt.Chat:
                # TODO вывести сообщение что пользователь ускользнул от правосудия под видом канала и предложить ввести команду для бана участника
                pass
    else:
        logger.info(f"{user.id} is innocent. Punishment time is {punishment_time}")
        await client.send_photo(
            chat_id,
            "./static/justified.jpg",
            reply_to_message_id=reply_to.id,
            caption=justified_caption,
        )
        return False


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
    await client.edit_message_reply_markup(
        chat_id,
        msg_id,
        reply_markup=pt.InlineKeyboardMarkup([[pt.InlineKeyboardButton(data, "void")]]),
    )


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
                    doc = col.insert_one(
                        {
                            "img_hash": str(hash),
                            "message_id": msg.id,
                            "file_id": msg.photo.file_id,
                            "is_active": True,
                        }
                    )
                    logger.info(f"Inserted document {doc.inserted_id} to db")
                except mongo_errors.DuplicateKeyError:
                    logger.warning("Hash already in DB")

                    logger.info("Getting duplicate image")
                    bayan = col.find_one_and_update(
                        {"img_hash": str(hash)}, {"$set": {"message_id": msg.id}}
                    )

                    logger.info("Creating directory and save collisions")
                    dir_name = f'{msg.id}_{bayan["message_id"]}'
                    await client.download_media(
                        msg.photo, f"./media/collisions/{dir_name}/"
                    )
                    await client.download_media(
                        bayan["file_id"], f"./media/collisions/{dir_name}/"
                    )
