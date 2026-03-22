# OSINT Regional Threat Pipeline (Multilingual)

![OSINT Dashboard Preview](https://img.shields.io/badge/Status-Project_Complete-brightgreen)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)
![React 18](https://img.shields.io/badge/React-18-58c4dc)
![Claude 3.5](https://img.shields.io/badge/Intelligence-Claude_3.5_Sonnet-orange)

A production-grade, asynchronous intelligence pipeline for monitoring South Asian regional security threats. This system scrapes real-time news across **Hindi, Urdu, Bengali, and Punjabi**, performs AI-driven translation, and generates deep-structured JSON intelligence briefs via Claude 3.5 Sonnet.

## 🚀 Core Features

-   **Multilingual Pipeline**: Staggered ingestion covering 4 major Indic languages with automated language detection.
-   **Intelligence Analysis**: Specialized Claude 3.5 Sonnet engine producing structured JSON briefs with threat categories, entities, and recommended actions.
-   **Real-time Dashboard**: A premium, glassmorphism-inspired React dashboard with WebSocket integration for live threat monitoring.
-   **Security-First**: JWT-based analyst authentication and RESTRICTED data classification by default.
-   **Compliance & Reliability**: 
    -   `robots.txt` compliance checking with local Redis caching.
    -   SHA-256 body-hash deduplication to prevent redundant analysis.
    -   IndicTrans2 (Hugging Face) + Sarvam AI fallback for best-in-class translation.

## 🛠 Tech Stack

-   **Backend**: Python 3.11, FastAPI, Celery
-   **Database**: PostgreSQL 16 + `pgvector` (for future similarity search)
-   **Cache/Queue**: Redis 7
-   **Frontend**: React 18, Vite, Lucide Icons
-   **AI/NLP**: Anthropic Claude 3.5 Sonnet, IndicTrans2, Sarvam AI, spaCy, Trafilatura

## 📂 Project Structure

```text
├── app/
│   ├── auth/           # JWT Security logic
│   ├── models/         # SQLAlchemy 2.0 ORM (Async)
│   ├── routes/         # Regional API endpoints (REST & WebSocket)
│   ├── tasks/          # Distributed pipeline (Scraper -> Analyst)
│   └── utils/          # Deduplication & Compliance helpers
├── frontend/           # React dashboard with modern UI/UX
├── sources.yaml        # Language-specific RSS and keyword config
├── requirements.txt    # Backend dependencies
└── .env.example        # Environment template
```

## ⚙️ Local Setup

### 1. Prerequisites
-   **PostgreSQL** (with `pgvector` extension)
-   **Redis** (v6+)
-   **Python 3.11+**
-   **Node.js v18+**

### 2. Configure Environment
```bash
cp .env.example .env
# Open .env and add your API keys:
# - ANTHROPIC_API_KEY
# - HUGGINGFACE_API_KEY
# - SARVAM_API_KEY
```

### 3. Backend Setup
```bash
pip install -r requirements.txt
python -m spacy download xx_ent_wiki_sm
# Start API
uvicorn app.main:app --reload
# Start Celery (separate terminals)
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🛰 Intelligence Feed

The dashboard streams new briefs in real-time. For manual testing, use the ingest bar to process any regional news URL.

---
Built for high situational awareness in South Asian regional security.
