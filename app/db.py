from config import MONGO_PASSWORD, MONGO_USERNAME
from pymongo import MongoClient, cursor

MONGO_CONN_STR = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@mongodb:27017"


class MongoConnection:
    def __init__(self):
        self.client = self._get_client()

    def _get_client(self):
        client = MongoClient(MONGO_CONN_STR)
        return client["bolice"]

    def __getitem__(self, col_name: str) -> cursor.Cursor:
        col = self.client[col_name]
        if len(list(col.list_indexes())) < 2:
            col.create_index([("img_hash", 1)], unique=True)
            col.create_index([("img_hash", 1), ("is_active", 1)])
            col.create_index([("message_id", 1)])
        return col
