from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from ..tasks.scraper import fetch_article_content
from ..tasks.preprocessor import preprocess_article
from ..models import RawArticle, ArticleStatus
from ..database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
from datetime import datetime

router = APIRouter()

class IngestRequest(BaseModel):
    url: HttpUrl
    language: str

@router.post("/manual")
async def ingest_manual(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    url = str(request.url)
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    
    # Check if exists
    from sqlalchemy import select
    existing = await db.execute(select(RawArticle).where(RawArticle.url_hash == url_hash))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Article already exists")

    # This is a bit slow for a sync-ish response, but okay for manual ingest demonstration
    raw_text = await fetch_article_content(url)
    if not raw_text:
        raise HTTPException(status_code=400, detail="Failed to extract content from URL")

    body_hash = hashlib.sha256(raw_text.encode()).hexdigest()
    
    new_article = RawArticle(
        url=url,
        url_hash=url_hash,
        body_hash=body_hash,
        raw_text=raw_text,
        language=request.language,
        status=ArticleStatus.PENDING
    )
    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)

    # Trigger pipeline
    preprocess_article.delay(new_article.id)

    return {"message": "Ingestion started", "article_id": new_article.id}
