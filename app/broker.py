import redis.asyncio as redis

from config import REDIS_HOST

redis_db = redis.from_url(REDIS_HOST)
