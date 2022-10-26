from pymongo import MongoClient, cursor
from config import MONGO_USERNAME, MONGO_PASSWORD


MONGO_CONN_STR = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@localhost:27017"

class MongoConnection:

    def __init__(self):
        self.client = self._get_client()

    def _get_client(self):
        client = MongoClient(MONGO_CONN_STR)
        return client["bolice"]

    def __getitem__(self, col_name: str) -> cursor.Cursor:
        col = self.client[col_name]
        col.create_index("img_hash", unique=True)
        return col
