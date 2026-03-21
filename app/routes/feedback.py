from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from ..database import get_db
from ..models import Brief, AnalystFeedback
from ..auth.jwt import get_current_user
import uuid

router = APIRouter()

class FeedbackRequest(BaseModel):
    override_urgency: Optional[str] = None
    override_category: Optional[str] = None
    notes: str

@router.post("/{brief_id}/feedback")
async def post_feedback(
    brief_id: uuid.UUID,
    feedback: FeedbackRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check if brief exists
    from sqlalchemy import select
    result = await db.execute(select(Brief).where(Brief.id == brief_id))
    brief = result.scalars().first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    new_feedback = AnalystFeedback(
        brief_id=brief_id,
        analyst_id=current_user.username,
        override_urgency=feedback.override_urgency,
        override_category=feedback.override_category,
        notes=feedback.notes
    )
    db.add(new_feedback)
    await db.commit()
    
    return {"message": "Feedback recorded"}

from typing import Optional
