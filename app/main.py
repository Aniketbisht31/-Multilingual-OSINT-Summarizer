from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db, engine
from .models import Base
from .routes import ingest, briefs, health
import asyncio

app = FastAPI(title="OSINT Regional Threat Pipeline", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Initial table creation (In production use Alembic)
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Careful!
        await conn.run_sync(Base.metadata.create_all)

app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(briefs.router, prefix="/briefs", tags=["Briefs"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(websocket.router, prefix="/ws", tags=["Real-time"])
app.include_router(feedback.router, prefix="/briefs", tags=["Briefs"])

@app.get("/")
async def root():
    return {"message": "Welcome to the OSINT Regional Threat Pipeline API"}
