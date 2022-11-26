from config import MONGO_HOST, MONGO_PASSWORD, MONGO_USERNAME
from pymongo import MongoClient, cursor

MONGO_CONN_STR = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:27017"


class MongoConnection:
    def __init__(self, chat_id):
        self.client = self._get_client(chat_id)

    def _get_client(self, chat_id):
        client = MongoClient(MONGO_CONN_STR)
        return client[chat_id]

    def get_history_collection(self):
        col = self.client["history"]
        if len(list(col.list_indexes())) < 2:
            col.create_index([("img_hash", 1)], unique=True)
            col.create_index([("img_hash", 1), ("is_active", 1)])
            col.create_index([("message_id", 1)])
        return col
