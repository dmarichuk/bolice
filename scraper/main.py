import os
import redis.asyncio as redis
from pyrogram.client import Client
from pyrogram import filters


redis_db = redis.from_url("redis://redis")

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
app = Client("bayanist", api_id=api_id, api_hash=api_hash)

CHANNELS_TO_LISTEN = set([int(chat_id) for chat_id in os.getenv("CHANNELS_TO_LISTEN").split(",")])
MAX_QUEUE_CAPACITY = 250
QUEUE_NAME = "memes_queue"


def specific_channel_filter(_, __, message):
    return message.chat.id in CHANNELS_TO_LISTEN

is_chosen_channel = filters.create(specific_channel_filter)


async def add_meme_to_queue(data):
    if await redis_db.llen(QUEUE_NAME) >= MAX_QUEUE_CAPACITY:
        await redis_db.rpop(QUEUE_NAME)
    await redis_db.lpush(QUEUE_NAME, data)


@app.on_message(filters.channel & is_chosen_channel & filters.photo)
async def await_memes(client, message):
    f = await client.download_media(message.photo, in_memory=True)
    await add_meme_to_queue(f.getvalue())


if __name__ == "__main__":
    app.run()
