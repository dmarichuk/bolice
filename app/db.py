from pymongo import MongoClient, cursor

MONGO_CONN_STR = "mongodb://superuser:superpassword@localhost:27017"

class MongoConnection:

    def __init__(self):
        self.client = self._get_client()

    def _get_client(self):
        client = MongoClient(MONGO_CONN_STR)
        return client["bolice"]

    def __getitem__(self, col_name: str) -> cursor.Cursor:
        col = self.client[col_name]
        col.create_index("img_hash")
        return col
