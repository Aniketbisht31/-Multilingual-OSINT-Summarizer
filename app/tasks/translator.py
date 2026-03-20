import httpx
import asyncio
from .celery_app import celery_app
from .database import AsyncSessionLocal
from .models import ProcessedArticle
from .config import settings
from sqlalchemy import select

@celery_app.task(name="app.tasks.translator.translate_to_english")
def translate_to_english(processed_article_id: int):
    return asyncio.run(_translate_to_english_internal(processed_article_id))

async def _translate_to_english_internal(processed_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ProcessedArticle).where(ProcessedArticle.id == processed_id))
        processed = result.scalars().first()
        if not processed:
            return f"Processed article {processed_id} not found"

        # Mapping for IndicTrans2 language codes
        lang_map = {
            "hi": "hin_Deva",
            "ur": "urd_Arab",
            "bn": "ben_Beng",
            "pa": "pan_Guru"
        }
        src_lang = lang_map.get(processed.detected_lang, "hin_Deva")

        english_text = ""
        model_used = ""
        confidence = 1.0

        # Try IndicTrans2 (Hugging Face Inference API)
        try:
            headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
            payload = {
                "inputs": processed.cleaned_text[:1000], # HF expects "inputs"
                "parameters": {"src_lang": src_lang, "tgt_lang": "eng_Latn"}
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    settings.INDICTRANS2_ENDPOINT,
                    headers=headers if settings.HUGGINGFACE_API_KEY else {},
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # HF Inference API returns a list or direct string depending on model wrapper
                    if isinstance(data, list) and len(data) > 0:
                        english_text = data[0].get("generated_text", "")
                    elif isinstance(data, dict):
                        english_text = data.get("generated_text", "")
                    model_used = "IndicTrans2-HF"
        except Exception as e:
            print(f"Hugging Face IndicTrans2 failed: {e}")

        # Fallback to Sarvam if needed
        if not english_text and settings.SARVAM_API_KEY:
            try:
                # Mocking Sarvam API call structure
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://api.sarvam.ai/translate",
                        headers={"Authorization": f"Bearer {settings.SARVAM_API_KEY}"},
                        json={
                            "input": processed.cleaned_text,
                            "source_language_code": processed.detected_lang,
                            "target_language_code": "en"
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        english_text = data.get("translated_text", "")
                        model_used = "Sarvam-AI"
                        confidence = 0.8
            except Exception as e:
                print(f"Sarvam AI failed: {e}")

        if english_text:
            processed.translation_english = english_text
            processed.translation_model = model_used
            processed.translation_confidence = confidence
            if confidence < 0.6:
                processed.needs_human_review = True
            
            await session.commit()

            # Enqueue analysis
            from .analyst import analyse_with_claude
            analyse_with_claude.delay(processed.id)
            return f"Translated article {processed_id} using {model_used}"
        else:
            return f"Translation failed for {processed_id}"
