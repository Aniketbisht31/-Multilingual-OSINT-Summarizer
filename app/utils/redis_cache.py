from redis import asyncio as aioredis
from ..config import settings
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=False)

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: Any, expire: int = 1800):
        await self.redis.setex(key, expire, json.dumps(value))

cache = RedisCache(settings.REDIS_URL)
