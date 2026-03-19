import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import enum

class SourceType(enum.Enum):
    RSS = "RSS"
    SCRAPE = "SCRAPE"
    SOCIAL = "SOCIAL"

class ArticleStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"

class Base(DeclarativeBase):
    pass

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(1024))
    language: Mapped[str] = mapped_column(String(10))  # hi, ur, bn, pa
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType))
    credibility_score: Mapped[Optional[int]] = mapped_column(default=3)

class RawArticle(Base):
    __tablename__ = "raw_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id"))
    url: Mapped[str] = mapped_column(String(1024), unique=True)
    url_hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256
    body_hash: Mapped[str] = mapped_column(String(64), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    language: Mapped[str] = mapped_column(String(10))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[ArticleStatus] = mapped_column(SQLEnum(ArticleStatus), default=ArticleStatus.PENDING)

class ProcessedArticle(Base):
    __tablename__ = "processed_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_article_id: Mapped[int] = mapped_column(ForeignKey("raw_articles.id"))
    cleaned_text: Mapped[str] = mapped_column(Text)
    detected_lang: Mapped[str] = mapped_column(String(10))
    lang_confidence: Mapped[float] = mapped_column(Float)
    named_entities: Mapped[dict] = mapped_column(JSON) # List of dicts
    translation_english: Mapped[Optional[str]] = mapped_column(Text)
    translation_model: Mapped[Optional[str]] = mapped_column(String(100))
    translation_confidence: Mapped[Optional[float]] = mapped_column(Float)
    needs_human_review: Mapped[bool] = mapped_column(default=False)

class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    processed_article_id: Mapped[int] = mapped_column(ForeignKey("processed_articles.id"))
    brief_json: Mapped[dict] = mapped_column(JSON)
    urgency: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(50))
    sentiment: Mapped[str] = mapped_column(String(50))
    data_classification: Mapped[str] = mapped_column(String(50), default="RESTRICTED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536)) # For OpenAI embeddings

class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    brief_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("briefs.id"))
    analyst_id: Mapped[str] = mapped_column(String(100))
    override_urgency: Mapped[Optional[str]] = mapped_column(String(20))
    override_category: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
