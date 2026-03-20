import json
import anthropic
import asyncio
from sqlalchemy import select
from .celery_app import celery_app
from .database import AsyncSessionLocal
from .models import ProcessedArticle, Brief
from .config import settings

SYSTEM_PROMPT = """You are an OSINT intelligence analyst specialising in South Asian regional security.
You receive translated news articles originally published in Hindi, Urdu, Bengali,
or Punjabi. Your task is to produce a structured intelligence brief in strict JSON.

Analyse each article for:
- Threat indicators: armed activity, border incidents, civil unrest, cyber attacks,
  disinformation campaigns, infrastructure threats
- Key entities: named persons (with role/affiliation), organisations, locations
  (with coordinates if inferrable), dates and timelines
- Source credibility: assess reliability (state-controlled / independent /
  tabloid / social-unverified) on a 1-5 scale
- Sentiment: NEUTRAL / ALARMING / INFLAMMATORY / FACTUAL / SPECULATIVE
- Urgency: LOW / MEDIUM / HIGH / CRITICAL based on recency + specificity
- Cross-source signals: note if claim corroborates or contradicts other
  recent reports in the same threat category

Output ONLY valid JSON matching this schema — no prose, no markdown:

{
  "brief_id": "<uuid>",
  "source": {
    "url": "",
    "name": "",
    "original_language": "hi|ur|bn|pa",
    "published_at": "<ISO8601>",
    "credibility_score": 1-5,
    "credibility_rationale": ""
  },
  "threat_assessment": {
    "category": "ARMED_CONFLICT|CYBER|CIVIL_UNREST|DISINFO|BORDER|INFRA|NONE",
    "subcategory": "",
    "urgency": "LOW|MEDIUM|HIGH|CRITICAL",
    "confidence": 0.0-1.0,
    "sentiment": "NEUTRAL|ALARMING|INFLAMMATORY|FACTUAL|SPECULATIVE"
  },
  "summary": "<2-3 sentence English summary, analyst tone, no hedging>",
  "key_entities": [
    {"name": "", "type": "PERSON|ORG|LOCATION|EVENT", "role": "", "lat": null, "lon": null}
  ],
  "timeline": [
    {"date": "<ISO8601 or partial>", "event": ""}
  ],
  "recommended_action": "MONITOR|ESCALATE|FLAG_FOR_REVIEW|DISCARD",
  "analyst_notes": "<anything anomalous: translation uncertainty, missing context, etc>"
}"""

@celery_app.task(name="app.tasks.analyst.analyse_with_claude")
def analyse_with_claude(processed_id: int):
    return asyncio.run(_analyse_with_claude_internal(processed_id))

async def _analyse_with_claude_internal(processed_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ProcessedArticle).where(ProcessedArticle.id == processed_id))
        processed = result.scalars().first()
        if not processed or not processed.translation_english:
            return f"Processed article {processed_id} not found or not translated"

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        user_message = f"""Source: Unknown (originally {processed.detected_lang} → EN, confidence: {processed.translation_confidence})
Published: {datetime.utcnow().isoformat()}
Translated content:
---
{processed.translation_english}
---
Produce the intelligence brief JSON now."""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620", # Updated to current production stable
                system=SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": user_message}]
            )
            
            brief_content = response.content[0].text
            brief_data = json.loads(brief_content)
            
            # Extract basic fields for filtering
            urgency = brief_data.get("threat_assessment", {}).get("urgency", "LOW")
            category = brief_data.get("threat_assessment", {}).get("category", "NONE")
            sentiment = brief_data.get("threat_assessment", {}).get("sentiment", "NEUTRAL")

            new_brief = Brief(
                processed_article_id=processed.id,
                brief_json=brief_data,
                urgency=urgency,
                category=category,
                sentiment=sentiment,
                data_classification=settings.DATA_CLASSIFICATION
            )
            session.add(new_brief)
            await session.commit()
            
            return f"Created brief for article {processed_id}"

        except Exception as e:
            print(f"Claude analysis failed: {e}")
            return f"Analysis failed: {e}"

from datetime import datetime
