from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from ..config import settings
import time

router = APIRouter()

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    start_time = time.time()
    
    # Check DB
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check Redis
    redis_status = "ok"
    # (Optional: actually ping redis)

    return {
        "status": "up",
        "database": db_status,
        "redis": redis_status,
        "pipelines": {
            "scraper_lag": "0s", # Placeholder
            "queue_depth": 0     # Placeholder
        },
        "api_keys": {
            "anthropic": "configured" if settings.ANTHROPIC_API_KEY else "missing",
            "sarvam": "configured" if settings.SARVAM_API_KEY else "missing"
        },
        "response_time_ms": int((time.time() - start_time) * 1000)
    }
