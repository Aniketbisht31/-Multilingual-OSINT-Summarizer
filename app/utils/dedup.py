import hashlib
from sqlalchemy import select
from ..models import RawArticle
from sqlalchemy.ext.asyncio import AsyncSession

async def is_duplicate(session: AsyncSession, body_hash: str) -> bool:
    result = await session.execute(
        select(RawArticle.id).where(RawArticle.body_hash == body_hash)
    )
    return result.scalars().first() is not None

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
