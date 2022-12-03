import motor.motor_asyncio as motor_aio
from pymongo import MongoClient, cursor

from config import MONGO_HOST, MONGO_PASSWORD, MONGO_USERNAME

MONGO_CONN_STR = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:27017"


class MongoConnection:
    def __init__(self, chat_id):
        self.client = self._get_client(chat_id)

    def _get_client(self, chat_id):
        client = motor_aio.AsyncIOMotorClient(MONGO_CONN_STR)
        return client[chat_id]

    async def get_history_collection(self):
        col = self.client["history"]
        indexes = await col.index_information()
        if len(indexes) < 2:
            await col.create_index([("img_hash", 1)], unique=True)
            await col.create_index([("img_hash", 1), ("is_active", 1)])
            await col.create_index([("message_id", 1)])
        return col
