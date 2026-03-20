import asyncio
import hashlib
import yaml
import httpx
import feedparser
import random
from datetime import datetime
from typing import List, Dict
from newspaper import Article
from bs4 import BeautifulSoup
from sqlalchemy import select
from .celery_app import celery_app
from .database import AsyncSessionLocal
from .models import RawArticle, Source, SourceType, ArticleStatus
from .config import settings

async def get_or_create_source(session, name: str, url: str, language: str, source_type: SourceType):
    result = await session.execute(select(Source).where(Source.url == url))
    source = result.scalars().first()
    if not source:
        source = Source(name=name, url=url, language=language, source_type=source_type)
        session.add(source)
        await session.commit()
        await session.refresh(source)
    return source

async def fetch_article_content(url: str) -> str:
    # Basic newspaper3k fetch
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 200:
            return article.text
    except Exception as e:
        print(f"Newspaper3k failed for {url}: {e}")

    # Fallback to BeautifulSoup
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            # Very basic extraction - in production use trafilatura for better results
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"BS4 fallback failed for {url}: {e}")
        return ""

from .utils.robots import robots_cache
from .utils.dedup import is_duplicate, compute_hash

@celery_app.task(name="app.tasks.scraper.scrape_sources")
def scrape_sources():
    # Helper to run async code in sync Celery task
    return asyncio.run(_scrape_sources_internal())

async def _scrape_sources_internal():
    with open("sources.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    async with AsyncSessionLocal() as session:
        for lang, sources in config.items():
            # Process RSS feeds
            for feed_url in sources.get("rss", []):
                # Respect robots.txt
                if not await robots_cache.can_fetch("OSINTBot/1.0", feed_url):
                    print(f"Skipping {feed_url} due to robots.txt")
                    continue

                # Add jitter
                await asyncio.sleep(random.uniform(2, 5))
                
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        resp = await client.get(feed_url)
                        feed = feedparser.parse(resp.content)
                        
                        source = await get_or_create_source(
                            session, feed.feed.get("title", feed_url), feed_url, lang, SourceType.RSS
                        )

                        for entry in feed.entries:
                            url = entry.link
                            url_hash = compute_hash(url)
                            
                            # Check if url already exists
                            existing = await session.execute(select(RawArticle).where(RawArticle.url_hash == url_hash))
                            if existing.scalars().first():
                                continue

                            # Fetch full content
                            raw_text = await fetch_article_content(url)
                            if not raw_text:
                                continue

                            body_hash = compute_hash(raw_text)
                            # Dedup by body hash
                            if await is_duplicate(session, body_hash):
                                continue

                            new_article = RawArticle(
                                source_id=source.id,
                                url=url,
                                url_hash=url_hash,
                                body_hash=body_hash,
                                raw_text=raw_text,
                                language=lang,
                                published_at=datetime.utcnow(),
                                status=ArticleStatus.PENDING
                            )
                            session.add(new_article)
                            await session.commit()
                            
                            # Enqueue next task (preprocessor)
                            from .preprocessor import preprocess_article
                            preprocess_article.delay(new_article.id)

                except Exception as e:
                    print(f"Error scraping feed {feed_url}: {e}")

    return "Scraping cycle complete"
