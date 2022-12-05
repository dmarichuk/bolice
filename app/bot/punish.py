import asyncio
import datetime as dt
import random
import typing as t

from config import POLL_TIMER
from db import MongoConnection
from pyrogram import Client
from pyrogram import types as pt
from utils import get_custom_logger, translate_seconds_to_timer

from .common import define_user_from_message, edit_inline_button_with_void
from .users import User

logger = get_custom_logger("bot__punish")


async def activate_bolice(client: Client, chat_id: int, bayan_msg, orig_doc):
    logger.info(
        f"Bolice activated in chat {chat_id}. Message id {bayan_msg.id}, Document id {orig_doc['_id']}"
    )
    await client.send_photo(
        chat_id,
        photo="./static/bolice.jpg",
        caption="🚨🚨 ЗАМЕЧЕН БАЯН! 🚨🚨",
        reply_to_message_id=bayan_msg.id,
    )
    await client.send_message(
        chat_id, reply_to_message_id=orig_doc["message_id"], text="Оригинал"
    )

    sender = define_user_from_message(bayan_msg)
    is_executed = True
    match type(sender):
        case pt.User:
            is_executed = await get_judgment_poll(
                client, chat_id, sender, "БАЯН", POLL_TIMER
            )
        case pt.Chat:
            pass
        case _:
            logger.error(f"Unknow sender type {type(sender)}")
            pass

    if not is_executed:
        conn = MongoConnection(str(chat_id))
        col = await conn.get_history_collection()
        updated_doc = await col.find_one_and_update(
            {"hash": orig_doc["hash"]}, {"$set": {"is_active": False}}
        )
        logger.info(f"Deactivated document {updated_doc['_id']}")


async def get_judgment_poll(
    client: Client, chat_id: int, defendant: User, accusation: str, countdown: int
) -> bool:
    logger.info("Poll is activated")
    poll = await client.send_poll(
        chat_id,
        question=f"Обвинение: {accusation}",
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
    is_executed = await activate_execution(
        client,
        chat_id,
        defendant,
        pro,
        contra,
        f"ПРИГОВОРЕН К ЗАКЛЮЧЕНИЮ ЗА {accusation.upper()}!",
        "ПОЛНОСТЬЮ ОПРАВДАН",
        updated_poll,
    )
    return is_executed


async def activate_execution(
    client: Client,
    chat_id: int,
    user: User,
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
            "static/punish.jpg",
            reply_to_message_id=reply_to.id,
            caption=f"{punishment_caption} ВРЕМЯ ЗАКЛЮЧЕНИЯ - {translate_seconds_to_timer(punishment_time)}",
        )
        await client.restrict_chat_member(
            chat_id,
            user.id,
            permissions=pt.ChatPermissions(),
            until_date=dt.datetime.now() + dt.timedelta(seconds=punishment_time),
        )
        return True
    else:
        logger.info(f"{user.id} is innocent. Punishment time is {punishment_time}")
        await client.send_photo(
            chat_id,
            "./static/justified.jpg",
            reply_to_message_id=reply_to.id,
            caption=justified_caption,
        )
        return False


def execute_sentence(pro: int, contra: int) -> t.Tuple[bool, int]:
    try:
        ratio = contra / pro
    except ZeroDivisionError:
        return False, 0
    if ratio > 1:
        return False, 0
    else:
        punishment_time = get_punishment_time(ratio)
        return True, punishment_time


def get_punishment_time(ratio: float) -> int:
    random.seed(dt.datetime.now().second)
    if ratio == 0:
        return random.randint(60 * 15, 60 * 60 - 1)
    if ratio <= 0.33:
        return random.randint(60 * 10, 60 * 15)
    if ratio <= 0.66:
        return random.randint(60 * 5, 60 * 10)
    if ratio <= 1:
        return random.randint(60, 60 * 5)
