import urllib.robotparser
from redis import asyncio as aioredis
from ..config import settings
import asyncio

class RobotsTxtCache:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def can_fetch(self, user_agent: str, url: str) -> bool:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Check cache
        cache_key = f"robots_txt:{domain}"
        robots_content = await self.redis.get(cache_key)
        
        rp = urllib.robotparser.RobotFileParser()
        if robots_content:
            rp.parse(robots_content.splitlines())
        else:
            # Fetch and cache for 24h
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{domain}/robots.txt")
                    if resp.status_code == 200:
                        await self.redis.setex(cache_key, 86400, resp.text)
                        rp.parse(resp.text.splitlines())
                    else:
                        return True # Default allow if robots.txt missing
            except:
                return True # Default allow on error

        return rp.can_fetch(user_agent, url)

robots_cache = RobotsTxtCache(settings.REDIS_URL)
