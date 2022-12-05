from db import MongoConnection
from hash import get_image_hash, init_image
from pymongo.errors import DuplicateKeyError
from pyrogram import Client
from utils import get_custom_logger

logger = get_custom_logger("bot__parse")


async def parse_chat_photos(client: Client, chat_id: int):
    conn = MongoConnection(str(chat_id))
    col = await conn.get_history_collection()

    async with client:
        async for msg in client.get_chat_history(chat_id):
            if msg.photo:
                f = await client.download_media(msg.photo, in_memory=True)
                img = init_image(f)
                if not img:
                    logger.error("Couldn't initialize image")
                    continue
                hash = get_image_hash(img)
                try:
                    doc = await col.insert_one(
                        {
                            "hash": str(hash),
                            "message_id": msg.id,
                            "file_id": msg.photo.file_id,
                            "is_active": True,
                        }
                    )
                    logger.info(f"Inserted document {doc.inserted_id} to db")
                except DuplicateKeyError:
                    logger.warning("Hash already in DB")

                    logger.info("Updating duplicate image")
                    await col.find_one_and_update(
                        {"hash": str(hash)}, {"$set": {"message_id": msg.id}}
                    )
