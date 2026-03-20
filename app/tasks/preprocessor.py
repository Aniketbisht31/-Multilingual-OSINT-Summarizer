import spacy
from langdetect import detect_langs
from trafilatura import extract
from .celery_app import celery_app
from .database import AsyncSessionLocal
from .models import RawArticle, ProcessedArticle, ArticleStatus
from sqlalchemy import select
import asyncio

# Load spacy model globally
try:
    nlp = spacy.load("xx_ent_wiki_sm")
except:
    nlp = None

@celery_app.task(name="app.tasks.preprocessor.preprocess_article")
def preprocess_article(article_id: int):
    return asyncio.run(_preprocess_article_internal(article_id))

async def _preprocess_article_internal(article_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RawArticle).where(RawArticle.id == article_id))
        article = result.scalars().first()
        if not article:
            return f"Article {article_id} not found"

        # 1. Clean boilerplate
        cleaned_text = extract(article.raw_text) or article.raw_text

        # 2. Language Detection
        try:
            langs = detect_langs(cleaned_text)
            top_lang = langs[0] # Lang(hi, 0.999)
            detected_lang = top_lang.lang
            lang_confidence = top_lang.prob
        except:
            detected_lang = article.language
            lang_confidence = 0.5

        if lang_confidence < 0.8:
            # Fallback or reject if needed
            pass

        # 3. Named Entity Recognition (NER)
        entities = []
        if nlp:
            doc = nlp(cleaned_text[:5000]) # Limit to first 5k chars for speed
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_
                })

        # Create ProcessedArticle
        processed = ProcessedArticle(
            raw_article_id=article.id,
            cleaned_text=cleaned_text,
            detected_lang=detected_lang,
            lang_confidence=lang_confidence,
            named_entities=entities
        )
        session.add(processed)
        
        # Update RawArticle status
        article.status = ArticleStatus.DONE
        
        await session.commit()
        await session.refresh(processed)

        # Enqueue translation
        from .translator import translate_to_english
        translate_to_english.delay(processed.id)

    return f"Processed article {article_id}"
