from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from ..database import get_db
from ..models import Brief
import uuid

router = APIRouter()

@router.get("/")
async def get_briefs(
    urgency: Optional[str] = None,
    category: Optional[str] = None,
    lang: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Brief).order_by(desc(Brief.created_at))
    
    if urgency:
        query = query.where(Brief.urgency == urgency.upper())
    if category:
        query = query.where(Brief.category == category.upper())
    
    # Language filtering would require a join with RawArticle/ProcessedArticle
    # For now, let's just do urgency and category from the Brief model
    
    result = await db.execute(query.limit(limit).offset(offset))
    briefs = result.scalars().all()
    
    return [
        {
            "id": str(b.id),
            "urgency": b.urgency,
            "category": b.category,
            "sentiment": b.sentiment,
            "created_at": b.created_at,
            "brief": b.brief_json
        } for b in briefs
    ]

@router.get("/{brief_id}")
async def get_brief(brief_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brief).where(Brief.id == brief_id))
    brief = result.scalars().first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief.brief_json
