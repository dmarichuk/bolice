import re
from enum import Enum
import datetime as dt
from dataclasses import dataclass
from pyrogram import Client
from pyrogram import types as pt
from motor.motor_asyncio import AsyncIOMotorCursor, AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from db import MongoConnection
from utils import get_custom_logger
from config import TRIAL_LIMIT

logger = get_custom_logger("bot__users")

username_re = re.compile(r"^@?(?P<username>\w+)$", re.IGNORECASE)

tstamp = float


class UserType(Enum):
    TG_USER = "TG_USER"
    TG_CHAT = "TG_CHAT"


@dataclass
class User:
    id: int
    tg_type: UserType
    username: str
    on_trial: bool
    last_poll: tstamp

    @classmethod
    def from_dict(cls, d: dict):
        user_map = dict(
            id = d.get("id"),
            username = d.get("username"),
            tg_type = d.get("tg_type", UserType.TG_USER.value),
            on_trial = d.get("on_trial", False),
            last_poll = d.get("last_poll", 0),
        )
        return cls(**user_map)
    
    async def to_db(self, chat_id: int, conn: AsyncIOMotorClient = None):
        if not conn:
            conn = MongoConnection(str(chat_id))
        col = await conn.get_user_collection()
        try:
            await col.insert_one({
                "id": self.id,
                "username": self.username,
                "tg_type": self.tg_type,
                "on_trial": self.on_trial,
                "last_poll": self.last_poll
            })
        except DuplicateKeyError as e:
            await col.update_one(
                {"username": self.username},
                {"$set": {
                        "id": self.id,
                        "tg_type": self.tg_type,
                        "on_trial": self.on_trial,
                        "last_poll": self.last_poll
                    }
                }
            )
    
    def is_trial_available(self) -> tuple[bool, int]:
        now = dt.datetime.now()
        delta = (now - dt.datetime.fromtimestamp(self.last_poll)).total_seconds()
        if delta <= TRIAL_LIMIT:
            return False, delta
        return True, delta

    def __eq__(self, other) -> bool:
        if self.username == other.username:
            return True
        return False

        

def clean_username(raw: str) -> str:
    return username_re.search(raw).group("username")

async def get_user_from_chat(user: pt.User | pt.Chat | str, chat_id: int, client: Client, conn: AsyncIOMotorClient = None) -> User:
    if not conn:
        conn = MongoConnection(str(chat_id))

    match type(user):
        case pt.User:
            user = User.from_dict(user.__dict__)
            user.type = UserType.TG_USER.value
        case pt.Chat:
            user = User.from_dict(user.__dict__)
            user.type = UserType.TG_CHAT.value
        case str:
            username = clean_username(user)
            chat_member = await client.get_chat_member(chat_id, username)
            user = User.from_dict(chat_member.user.__dict__)
            user.type = UserType.TG_USER.value
    logger.info(user)
    col = await conn.get_user_collection()
    user_doc = await col.find_one({"username": user.username})
    if user_doc:
        return User.from_dict(user_doc)
    await user.to_db(chat_id, conn)
    return user
    