from pyrogram import Client
from pyrogram import types as pt

from utils import get_custom_logger

logger = get_custom_logger("bot__common")


def define_user_from_message(msg: pt.Message) -> pt.User | pt.Chat:
    if msg.from_user:
        return msg.from_user
    if msg.sender_chat:
        return msg.sender_chat
    return None


async def edit_inline_button_with_void(
    client: Client, chat_id: int, msg_id: int, data: str
):
    await client.edit_message_reply_markup(
        chat_id,
        msg_id,
        reply_markup=pt.InlineKeyboardMarkup([[pt.InlineKeyboardButton(data, "void")]]),
    )


class ExceedTranslationLimit(Exception):
    pass


def translate_seconds_to_timer(n: int) -> str:
    if n >= 60 * 60:
        raise ExceedTranslationLimit(f"{n} is greater than an hour")
    minute = n // 60
    seconds = n % 60
    return "{}:{}".format(str(minute).zfill(2), str(seconds).zfill(2))
