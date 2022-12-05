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
